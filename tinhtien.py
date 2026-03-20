import os
import logging

# Reduce Streamlit warning noise for bare mode execution
os.environ.setdefault("STREAMLIT_LOG_LEVEL", "error")
logging.getLogger("streamlit").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Cấu hình trang
st.set_page_config(page_title="Quản Lý Đội Bóng 2026", layout="wide")

# 1. TẠO DỮ LIỆU CÁC NGÀY THỨ 4 NĂM 2026
def get_wednesdays(year):
    d = datetime(year, 1, 1)
    d += timedelta(days=(2 - d.weekday() + 7) % 7)
    dates = []
    while d.year == year:
        dates.append(d)
        d += timedelta(days=7)
    return dates

all_wed_2026 = get_wednesdays(2026)
date_strings = [d.strftime('%d/%m/%Y') for d in all_wed_2026]

# 2. DANH SÁCH THÀNH VIÊN
members = ["Dũng", "Nam", "Hoàng", "Tuấn", "Minh", "Đức", "Sơn", "Hải"]

# 3. KHỞI TẠO SESSION STATE (LƯU TRỮ TẠM THỜI)
if 'df_ball' not in st.session_state:
    data = {"Thành viên": members}
    for ds in date_strings:
        data[ds] = False
    st.session_state.df_ball = pd.DataFrame(data)
    st.session_state.df_ball["Ghi chú"] = ""

# --- GIAO DIỆN CHÍNH ---
st.title("⚽ Quản Lý Đội Bóng & Thống Kê Tháng")

tab1, tab2 = st.tabs(["📝 Điểm danh theo ngày", "📊 Thống kê đóng tiền tháng"])

# TAB 1: ĐIỂM DANH HÀNG TUẦN
with tab1:
    col_date, col_save = st.columns([2, 1])
    with col_date:
        selected_date = st.selectbox("Chọn ngày Thứ 4:", date_strings)
    
    # Hiển thị bảng chỉnh sửa
    edited_df = st.data_editor(
        st.session_state.df_ball[["Thành viên", selected_date, "Ghi chú"]],
        column_config={
            selected_date: st.column_config.CheckboxColumn("Đã đóng?"),
            "Thành viên": st.column_config.TextColumn(disabled=True),
        },
        hide_index=True,
        use_container_width=True
    )

    if st.button("Lưu dữ liệu ngày này"):
        st.session_state.df_ball.update(edited_df)
        st.success(f"Đã lưu trạng thái ngày {selected_date}")

# TAB 2: THỐNG KÊ THEO THÁNG
with tab2:
    month_selected = st.selectbox("Chọn tháng cần xem:", range(1, 13), format_func=lambda x: f"Tháng {x}")
    
    # Lọc các cột Thứ 4 thuộc tháng đã chọn
    cols_in_month = [d.strftime('%d/%m/%Y') for d in all_wed_2026 if d.month == month_selected]
    
    if cols_in_month:
        st.write(f"Trong tháng {month_selected} có {len(cols_in_month)} trận (ngày: {', '.join(cols_in_month)})")
        
        # Tính toán dữ liệu tháng
        month_data = st.session_state.df_ball[["Thành viên"] + cols_in_month].copy()
        
        # Tạo cột "Số trận đã đóng"
        month_data["Số trận đã đóng"] = month_data[cols_in_month].sum(axis=1)
        
        # Xác định ai đã hoàn thành nghĩa vụ tháng (đóng đủ tất cả các buổi)
        full_paid = month_data[month_data["Số trận đã đóng"] == len(cols_in_month)]
        not_full = month_data[month_data["Số trận đã đóng"] < len(cols_in_month)]

        # Hiển thị Dashboard tháng
        c1, c2 = st.columns(2)
        with c1:
            st.success(f"✅ Đã đóng đủ tháng ({len(full_paid)})")
            if not full_paid.empty:
                st.write(", ".join(full_paid["Thành viên"].tolist()))
            else:
                st.write("Chưa có ai đóng đủ.")

        with c2:
            st.error(f"⚠️ Chưa đóng đủ tháng ({len(not_full)})")
            if not not_full.empty:
                st.write(", ".join(not_full["Thành viên"].tolist()))
        
        st.markdown("---")
        st.write("**Chi tiết đóng tiền trong tháng:**")
        st.dataframe(month_data, hide_index=True, use_container_width=True)
    else:
        st.warning("Không có dữ liệu cho tháng này.")

# NÚT XUẤT FILE CHO DÂN DATA
st.sidebar.markdown("### Quản lý dữ liệu")
csv = st.session_state.df_ball.to_csv(index=False).encode('utf-8-sig')
st.sidebar.download_button("📥 Tải File CSV Toàn Năm", data=csv, file_name='quy_bong_da_2026.csv')
