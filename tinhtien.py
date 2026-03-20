import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Quản Lý Đội Bóng FC Thứ 4", layout="wide")

# Kết nối Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- HÀM HỖ TRỢ ---
def get_all_wednesdays(year):
    d = datetime(year, 1, 1)
    d += timedelta(days=(2 - d.weekday() + 7) % 7)
    while d.year == year:
        yield d.strftime('%d/%m/%Y')
        d += timedelta(days=7)

wednesdays_2026 = list(get_all_wednesdays(2026))
# Cập nhật danh sách thành viên cố định của Duyên tại đây
fixed_members = ["Dũng", "Nam", "Hoàng", "Tuấn", "Minh", "Đức", "Sơn", "Hải"]

# Tải dữ liệu và xử lý ép kiểu
@st.cache_data(ttl=5) 
def load_data():
    try:
        df = conn.read(worksheet="Data", ttl="0")
        if df.empty:
            return pd.DataFrame(columns=["Ngày", "Thanh_vien", "Trang_thai", "Ghi_chu"])
        
        # BƯỚC QUAN TRỌNG: Ép kiểu để tránh lỗi Checkbox FLOAT
        df["Trang_thai"] = df["Trang_thai"].map({1: True, 0: False, "TRUE": True, "FALSE": False, True: True, False: False})
        df["Trang_thai"] = df["Trang_thai"].fillna(False).astype(bool)
        return df
    except:
        return pd.DataFrame(columns=["Ngày", "Thanh_vien", "Trang_thai", "Ghi_chu"])

df_master = load_data()

# --- GIAO DIỆN ---
st.title("⚽ Quản Lý Tiền Sân Đội Bóng 2026")

tab1, tab2 = st.tabs(["📝 Điểm danh & Ghi chú", "📊 Thống kê tháng"])

# TAB 1: ĐIỂM DANH THEO NGÀY
with tab1:
    selected_date = st.selectbox("Chọn ngày Thứ 4:", wednesdays_2026)
    
    # Lọc dữ liệu ngày được chọn
    df_today = df_master[df_master["Ngày"] == selected_date].copy()
    
    # Nếu ngày này hoàn toàn mới, tự động tạo danh sách mặc định
    if df_today.empty:
        df_today = pd.DataFrame({
            "Ngày": [selected_date] * len(fixed_members),
            "Thanh_vien": fixed_members,
            "Trang_thai": [False] * len(fixed_members),
            "Ghi_chu": [""] * len(fixed_members)
        })

    st.subheader(f"Danh sách đóng tiền ngày {selected_date}")
    
    # Bảng chỉnh sửa chính
    edited_df = st.data_editor(
        df_today[["Thanh_vien", "Trang_thai", "Ghi_chu"]],
        column_config={
            "Thanh_vien": st.column_config.TextColumn("Tên", disabled=True),
            "Trang_thai": st.column_config.CheckboxColumn("Đã đóng?"),
            "Ghi_chu": st.column_config.TextColumn("Ghi chú ngày này (Khách mời...)", width="large")
        },
        hide_index=True,
        use_container_width=True,
        key=f"editor_{selected_date}" # Key động theo ngày để tránh lẫn cache
    )

    # Thêm khách mời vãng lai
    with st.expander("➕ Thêm khách/người đi thêm hôm nay"):
        col_name, col_btn = st.columns([3, 1])
        guest_name = col_name.text_input("Tên người đi thêm:", key="guest_input")
        if col_btn.button("Thêm vào bảng"):
            if guest_name:
                new_row = pd.DataFrame({"Ngày": [selected_date], "Thanh_vien": [guest_name], "Trang_thai": [False], "Ghi_chu": ["Khách mời"]})
                df_master = pd.concat([df_master, new_row], ignore_index=True)
                st.rerun()

    # NÚT LƯU - ĐẨY LÊN GOOGLE SHEETS
    if st.button("💾 LƯU DỮ LIỆU VÀO GOOGLE SHEETS", type="primary"):
        with st.spinner("Đang đồng bộ..."):
            # Xóa bản ghi cũ của ngày này để ghi đè bản mới
            df_final = df_master[df_master["Ngày"] != selected_date]
            
            # Lấy dữ liệu từ bảng vừa edit
            df_new_today = edited_df.copy()
            df_new_today["Ngày"] = selected_date
            
            # Gộp lại và lưu
            df_save = pd.concat([df_final, df_new_today], ignore_index=True)
            conn.update(worksheet="Data", data=df_save)
            st.cache_data.clear()
            st.success(f"Đã lưu thành công dữ liệu ngày {selected_date}!")

# TAB 2: THỐNG KÊ THÁNG
with tab2:
    m_idx = datetime.now().month - 1
    month = st.selectbox("Chọn tháng:", range(1, 13), format_func=lambda x: f"Tháng {x}", index=m_idx)
    
    # Chuyển đổi cột Ngày sang datetime để lọc chính xác
    df_master['Date_Obj'] = pd.to_datetime(df_master['Ngày'], format='%d/%m/%Y', errors='coerce')
    df_month = df_master[df_master['Date_Obj'].dt.month == month]
    
    if not df_month.empty:
        summary = df_month.groupby("Thanh_vien").agg(
            So_buoi=("Ngày", "count"),
            Da_dong=("Trang_thai", "sum")
        ).reset_index()
        
        summary["Còn nợ (buổi)"] = summary["So_buoi"] - summary["Da_dong"]
        
        st.write(f"### Báo cáo quỹ tháng {month}")
        st.dataframe(summary.sort_values("Còn nợ (buổi)"), use_container_width=True, hide_index=True)
        
        st.write("📝 **Chi tiết ghi chú/khách mời tháng này:**")
        st.dataframe(df_month[df_month["Ghi_chu"] != ""][["Ngày", "Thanh_vien", "Ghi_chu"]], hide_index=True)
    else:
        st.info("Chưa có dữ liệu đóng tiền cho tháng này.")
