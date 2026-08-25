# Review and Citation Recommendations: Predictive Uncertainty Quantification

**Target File:** `sections/methods006.tex`
**Subsection:** `\subsection{Predictive uncertainty quantification}`

Dựa trên việc rà soát nội dung của subsection và so sánh với kho dữ liệu `temp.bib` cũng như `writing_manu2.bib`, dưới đây là các gợi ý bổ sung và điều chỉnh trích dẫn để tăng tính học thuật và sự chặt chẽ cho phần Định lượng Độ bất định (Predictive Uncertainty Quantification).

## 1. Củng cố lý thuyết về Posterior Predictive Distribution
**Vị trí:**
> "... which combines variation not explained by the regression model with uncertainty in the fitted regression coefficients `\citep{mackay_bayesian_1992}`."

**Nhận xét:**
MacKay (1992) là một trích dẫn kinh điển rất tốt, nhưng khi trình bày về "posterior predictive distribution" dưới góc độ xác suất và hồi quy tuyến tính Bayesian, việc bổ sung thêm các sách giáo khoa nền tảng (đã có sẵn trong thư viện của bạn) sẽ giúp khẳng định độ tin cậy của phương pháp.

**Gợi ý sửa thành:**
> "... which combines variation not explained by the regression model with uncertainty in the fitted regression coefficients `\citep{mackay_bayesian_1992, bishop_pattern_2006, gelman_bayesian_2013}`."

## 2. Bổ sung lý thuyết cho Point Estimate (Ước lượng điểm)
**Vị trí:**
> `The corresponding point estimate was`
> `\widehat{\Delta d}_{s,*} = \mu_{s,*}.`

**Nhận xét:**
Bạn có thể giải thích thêm (nếu không bị giới hạn từ ngữ) rằng việc chọn trung bình dự báo (predictive mean) làm điểm ước lượng (point estimate) là quyết định tối ưu theo hàm mất mát bình phương (squared loss function) trong lý thuyết quyết định Bayesian (Bayesian decision theory). 

**Gợi ý bổ sung câu dẫn:**
> "Under a squared-error loss function, the optimal point estimate is given by the predictive mean `\citep{bishop_pattern_2006}`:"

## 3. Khoảng tin cậy (Coverage và Sharpness)
**Vị trí:**
> "Both measures were examined because a wider interval may enclose more observations while providing less precise information `\citep{singh_uncertainty_2024}`."

**Nhận xét:**
`singh_uncertainty_2024` rất phù hợp cho ứng dụng Machine Learning trong quan trắc Trái Đất. Tuy nhiên, nguyên lý cơ bản của việc cân bằng giữa "empirical coverage" (calibration) và "interval width" (sharpness) được định nghĩa rất chuẩn mực bởi Gneiting et al. (2007). Bài báo này là kim chỉ nam cho việc đánh giá dự báo xác suất (probabilistic forecasts). Mặc dù nó chưa có trong `temp.bib`, tui khuyên bạn nên bổ sung nó vào `writing_manu2.bib`.

**Gợi ý sửa thành:**
> "Both measures were examined because a wider interval may enclose more observations while providing less precise information `\citep{gneiting_probabilistic_2007, singh_uncertainty_2024}`."

**BibTeX entry để bạn tham khảo thêm vào `writing_manu2.bib`:**
```bibtex
@article{gneiting_probabilistic_2007,
  title = {Probabilistic Forecasts, Calibration and Sharpness},
  author = {Gneiting, Tilmann and Balabdaoui, Fadoua and Raftery, Adrian E.},
  year = {2007},
  journal = {Journal of the Royal Statistical Society: Series B (Statistical Methodology)},
  volume = {69},
  number = {2},
  pages = {243--268},
  doi = {10.1111/j.1467-9868.2007.00587.x}
}
```

## 4. Giải thích nguyên nhân sai lệch Coverage (Temporal Dependence)
**Vị trí:**
> "Temporal dependence and relations not represented by the regression model could cause the empirical coverage to differ from the nominal level."

**Nhận xét:**
Đây là một nhận định rất sắc bén và chính xác. Sự tương quan chuỗi thời gian (autocorrelation/temporal dependence) không được mô hình hóa thường dẫn đến việc các mô hình đánh giá quá thấp (underestimate) độ bất định (phương sai), làm cho khoảng dự báo bị hẹp lại và empirical coverage thấp hơn nominal level. Bạn có thể chèn thêm trích dẫn về ảnh hưởng của cấu trúc sai số (model misspecification) lên posterior predictive intervals. `gelman_bayesian_2013` có đề cập sâu đến vấn đề này ở chương đánh giá mô hình.

**Gợi ý sửa thành:**
> "Temporal dependence and relations not represented by the regression model could cause the empirical coverage to differ from the nominal level `\citep{gelman_bayesian_2013}`."

---
**Tóm tắt:**
Phần trình bày toán học và cấu trúc của `\subsection{Predictive uncertainty quantification}` hiện tại đã rất chặt chẽ và chuẩn xác. Các gợi ý trên chủ yếu là chèn thêm trích dẫn (citations) vào các chỗ trống lý thuyết để bài viết "nặng ký" hơn dưới góc nhìn của reviewers. Bạn có thể yêu cầu trợ lý xem xét và áp dụng các thay đổi này vào `methods006.tex`.
