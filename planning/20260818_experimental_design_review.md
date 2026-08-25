# Review: Experimental Design

**Target File:** `sections/methods006.tex`
**Subsection:** `\subsection{Experimental design}`

## Nhận xét tổng quan (Verdict: Keep & Polish)
Vì thiết kế 3 nhánh (3-arm backtest: delayed-label, sparse measurement, permanent stoppage) là cốt lõi đóng góp của nghiên cứu nhằm giải quyết bài toán "mạng lưới quan trắc đang lụi tàn" (dying network constraint), việc **không có trích dẫn dày đặc ở phần này là hoàn toàn hợp lý và nên được giữ nguyên**. Nó làm nổi bật tính nguyên bản (originality) của phương pháp tiếp cận.

Tuy nhiên, để phòng hờ trường hợp reviewer hỏi vặn "Tại sao không dùng k-fold cross-validation thông thường?", bạn có thể neo (anchor) một vài trích dẫn cơ bản vào các nguyên lý nền tảng.

## Gợi ý điều chỉnh nhỏ (Lightweight Mode)

### 1. Khẳng định nguyên lý Walk-Forward Validation
**Vị trí:**
> "All three evaluation designs preserved the temporal order of the monitoring records... This design prevented later MLCW observations from influencing earlier estimates."

**Nhận xét:**
Đây là mô tả kinh điển của "walk-forward validation" hay "out-of-sample temporal testing". Bạn có thể chèn nhẹ một trích dẫn sách giáo khoa để reviewer thấy rằng quyết định không dùng random k-fold là có cơ sở khoa học, tránh rò rỉ dữ liệu (data leakage).

**Gợi ý sửa thành:**
> "All three evaluation designs preserved the temporal order of the monitoring records to prevent data leakage `\citep{hastie_elements_2009}`. For each period being estimated..."

### 2. Phương trình gộp phương sai (Variance Accumulation)
**Vị trí:**
> `\Cref{eq:cumulative_residual_distribution}` đến `\Cref{eq:scaled_cumulative_residual}`

**Nhận xét:**
Các phương trình biến đổi để chuẩn hóa phương sai tích lũy (`\sqrt{H_I}`) là một phép dẫn xuất (derivation) toán học chuẩn mực từ tính chất của phân phối chuẩn (tổng các biến ngẫu nhiên độc lập). Bạn đã trình bày các bước rất rõ ràng. **Không cần trích dẫn thêm**, vì đây là kiến thức nền tảng của thống kê và chính việc tự dẫn giải trong bài đã cho thấy sự vững vàng của mô hình.

### 3. Cumulative vs Point-in-time
**Vị trí:**
> "Because a 6-month schedule and a 12-month schedule complete different numbers of measurement intervals..."

**Nhận xét:**
Lập luận đánh giá sự khác biệt về tần suất đo đạc được viết rất logic và chặt chẽ. Cách thiết kế endpoint chia sẻ chung (shared calibration endpoint) giúp phép so sánh công bằng. Thiết kế này đặc thù cho dự án Tuku nên là "own contribution", không cần và không nên trích dẫn ai khác ở đây.

---
**Kết luận:** 
Phần này đã đạt chuẩn để nộp (submission-ready). Tính nguyên bản của thiết kế thực nghiệm là điểm sáng lớn nhất. Bạn chỉ cần cân nhắc chèn thêm `\citep{hastie_elements_2009}` vào dòng đầu tiên để chốt chặn các câu hỏi về data leakage, còn lại hãy giữ nguyên hoàn toàn.
