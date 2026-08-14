# Ví dụ tính bằng tay cho hai chu kỳ đo MLCW giãn cách

**Thời gian ghi chú:** 2026/08/10 14:32:58
**Phần được giải thích:** Section 3.4.2 trong `sections/methods005.tex`
**Mục đích của tài liệu này:** Đây là tài liệu dạy học, giúp người đọc hiểu cơ chế bên trong thuật toán trước khi đọc phần Methods chính thức của bản thảo. Ví dụ dùng số liệu nhỏ, tự đặt ra, để có thể tính tay từng bước. Số liệu này không phải số liệu thật từ trạm TUKU.

## 1. Bài toán cần giải quyết

Trạm quan trắc MLCW (multi-layer compaction well — giếng quan trắc lún nhiều tầng) đôi khi không đo được hàng tháng. Có tháng có số liệu, có tháng chỉ có một phép đo tổng gộp sau một khoảng thời gian dài. Câu hỏi đặt ra là: khi mô hình đã học từ vài tháng có số liệu đầy đủ, rồi sau đó chỉ nhận được một con số tổng (không phải từng tháng), làm sao dùng con số tổng đó để cập nhật lại mô hình cho đúng?

Ví dụ này trả lời câu hỏi đó bằng một trường hợp nhỏ nhất có thể: chỉ xét **một lớp đất (depth section)**, và chỉ chạy qua **hai chu kỳ liên tiếp**.

Sáu bước xảy ra theo đúng thứ tự sau:

1. Dùng 5 quan sát hàng tháng tại các mốc thời gian $k_1$ đến $k_5$ để huấn luyện mô hình lần đầu.
2. Dùng mô hình đó để ước tính độ lún hàng tháng (monthly deformation increment) tại $k_6$, $k_7$, $k_8$ — ba tháng mà mô hình **chưa biết đáp án thật**.
3. Cuối ba tháng đó, nhận được một phép đo mới: độ lún tích lũy (cumulative displacement) tính từ đầu đến cuối khoảng. Lấy hiệu giữa điểm cuối và điểm đầu, ta biết tổng độ lún của cả ba tháng cộng lại — nhưng không biết riêng từng tháng lún bao nhiêu.
4. Đưa con số tổng này vào tập dữ liệu huấn luyện, dưới dạng một ràng buộc theo khoảng (interval constraint), rồi huấn luyện lại mô hình từ đầu.
5. Dùng mô hình vừa cập nhật để ước tính tiếp ba tháng kế, $k_9$, $k_{10}$, $k_{11}$.
6. Cuối khoảng thứ hai này, lại nhận một phép đo tổng mới, lại thêm vào tập huấn luyện, lại huấn luyện lại mô hình.

Một điểm cần lưu ý về cách đặt tên: hai phép đo tổng ở bước 3 và bước 6 **không** được gọi là $k_9$ và $k_{13}$ (dù chúng cũng xảy ra ở những mốc thời gian đó). Lý do là nếu gọi vậy, người đọc dễ nhầm một phép đo tổng ba tháng với một phép đo lún của riêng một tháng — hai thứ này có ý nghĩa vật lý khác hẳn nhau. Vì vậy, tài liệu này dùng ký hiệu riêng: $\Delta d_{I_1}$ cho phép đo tổng của khoảng thứ nhất, $\Delta d_{I_2}$ cho khoảng thứ hai.

## 2. Những gì ví dụ này đã đơn giản hóa so với mô hình thật

Mô hình thật dùng nhiều biến đầu vào (predictor) cùng lúc — ví dụ như biến dạng bề mặt, mực nước ngầm, lượng mưa. Ví dụ này chỉ dùng **một** biến đầu vào duy nhất, ký hiệu $x_k$, để phép tính có thể làm bằng tay trên giấy. Có thể hình dung $x_k$ là một biến động lực hàng tháng bất kỳ, đã được quy về cùng một thang đo với mô hình. Khi mô hình thật dùng nhiều biến, $x_k$ chỉ cần thay bằng một vector $\boldsymbol{x}_k$ (tức là một danh sách nhiều số thay vì một số) — các bước tính toán còn lại giữ nguyên, không đổi.

Mô hình Bayesian ridge regression có hai tham số kiểm soát mức độ tin tưởng vào dữ liệu và mức độ co hệ số về không, gọi là residual precision ($\alpha$) và coefficient precision ($\lambda$). Ví dụ này cố định luôn hai giá trị này bằng 1:

$$
\alpha=1,
\qquad
\lambda=1.
$$

Trong quy trình xử lý thật, hai giá trị này không cố định — chúng được ước lượng lại từ chính dữ liệu mỗi lần mô hình huấn luyện lại. Ở đây, chúng được giữ cố định chỉ để phép tính tay đơn giản và có thể kiểm tra lại từng bước bằng máy tính cầm tay.

## 3. Viết mô hình dưới dạng công thức

Độ lún hàng tháng tại một mốc thời gian $k$ (monthly deformation increment) được mô hình hóa như sau:

$$
\Delta d_k
=
\beta_1x_k+
\beta_0+
\varepsilon_k.
$$

Công thức này nói rằng: độ lún tháng đó bằng biến đầu vào $x_k$ nhân với một hệ số góc $\beta_1$, cộng với một hằng số $\beta_0$ (intercept — giá trị nền khi $x_k=0$), cộng thêm phần sai số ngẫu nhiên $\varepsilon_k$ mà mô hình không giải thích được.

Hai hệ số cần tìm ($\beta_1$ và $\beta_0$) được gộp thành một vector, viết theo thứ tự hệ số góc trước rồi đến hằng số:

$$
\boldsymbol{\beta}
=
\begin{bmatrix}
\beta_1\\
\beta_0
\end{bmatrix}.
$$

Mỗi quan sát hàng tháng tạo ra một hàng dữ liệu trong bảng huấn luyện (regression row), gồm giá trị $x_k$ và số 1 (đại diện cho hằng số):

$$
\boldsymbol{z}_k
=
\begin{bmatrix}
x_k & 1
\end{bmatrix}.
$$

Bayesian ridge regression không chỉ cho ra một con số ước lượng duy nhất cho $\boldsymbol{\beta}$, mà cho ra cả một phân bố xác suất quanh giá trị đó — phần trung tâm của phân bố này gọi là posterior mean (giá trị trung bình hậu nghiệm), độ rộng của phân bố gọi là posterior covariance (hiệp phương sai hậu nghiệm). Hai đại lượng này được tính bằng công thức chuẩn:

$$
\boldsymbol{\Sigma}
=
\left(
\lambda\boldsymbol{I}
+
\alpha\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{Z}
\right)^{-1},
$$

Công thức này trông rối vì có 4 ký hiệu lạ đứng cùng nhau. Đi từng ký hiệu một trước khi ghép lại.

$\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{Z}$ là lượng thông tin mà dữ liệu đã đo được cung cấp. $\boldsymbol{Z}$ là bảng dữ liệu huấn luyện, gồm tất cả các hàng $\boldsymbol{z}_k$ xếp chồng lên nhau — mỗi hàng là một tháng quan sát. Nhân $\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{Z}$ (ma trận $\boldsymbol{Z}$ nhân với chính nó, sau khi lật hàng thành cột) cho ra một ma trận nhỏ tóm tắt: dữ liệu đã thu thập được trải rộng và đa dạng đến đâu. Càng có nhiều tháng quan sát, và các tháng đó càng khác nhau về giá trị $x_k$, ma trận này càng "lớn" theo nghĩa mang nhiều thông tin.

$\alpha$ là độ tin cậy vào từng phép đo — tức là mô hình tin dữ liệu quan sát được đến mức nào, ngược với mức độ nhiễu (residual precision, đại lượng nghịch đảo của variance nhiễu). $\alpha$ càng lớn nghĩa là mô hình coi dữ liệu càng ít nhiễu, càng đáng tin. Nhân $\alpha$ vào $\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{Z}$ nghĩa là: lượng thông tin từ dữ liệu được cân theo mức độ tin cậy vào dữ liệu đó.

$\lambda\boldsymbol{I}$ là phần "phanh an toàn" được cộng thêm trước khi làm phép nghịch đảo. $\boldsymbol{I}$ là ma trận đơn vị (identity matrix) — có thể hình dung nó như số 1 trong đại số ma trận, không làm thay đổi hướng của bất kỳ vector nào khi nhân vào. $\lambda$ là mức độ co hệ số về không (coefficient precision) — $\lambda$ càng lớn, mô hình càng ép các hệ số $\boldsymbol{\beta}$ về gần 0, tức là càng thận trọng, càng ít tin vào các hệ số lớn bất thường.

Đây chính là chữ "ridge" trong tên Bayesian ridge regression. Nếu chỉ dùng $\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{Z}$ mà không cộng thêm $\lambda\boldsymbol{I}$, có hai tình huống dễ xảy ra khi dữ liệu ít hoặc các biến đầu vào trùng lặp thông tin với nhau: ma trận $\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{Z}$ có thể không nghịch đảo được (giống như chia cho 0), hoặc nghịch đảo được nhưng cho ra hệ số $\boldsymbol{\beta}$ lớn bất thường, không đáng tin. Cộng thêm $\lambda\boldsymbol{I}$ trước khi nghịch đảo giống như thêm một chút "trọng lượng nền" vào ma trận, đảm bảo phép nghịch đảo luôn tính được, và giữ hệ số không bùng nổ ra những giá trị vô lý. Đây là một dạng phanh an toàn được cài sẵn vào công thức, không phải một bước sửa lỗi thêm vào sau.

Dấu $(\cdot)^{-1}$ ở ngoài cùng là phép nghịch đảo ma trận (matrix inverse) — làm việc tương tự phép chia trong số học thường, nhưng áp dụng cho ma trận. Nếu nhân một ma trận với nghịch đảo của chính nó, kết quả luôn là ma trận đơn vị $\boldsymbol{I}$, giống như một số nhân với nghịch đảo của nó luôn bằng 1.

Ghép cả ba phần lại: $\boldsymbol{\Sigma}$ là kết quả của phép nghịch đảo áp lên tổng của "phanh an toàn" ($\lambda\boldsymbol{I}$) và "lượng thông tin từ dữ liệu, đã cân theo độ tin cậy" ($\alpha\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{Z}$).

$\boldsymbol{\Sigma}$ chính là độ không chắc chắn còn lại quanh hệ số $\boldsymbol{\beta}$, sau khi đã học từ dữ liệu. Nếu $\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{Z}$ lớn — tức là có nhiều quan sát, đa dạng — thì tổng bên trong dấu ngoặc lớn, nghịch đảo của một số lớn là một số nhỏ, nên $\boldsymbol{\Sigma}$ nhỏ. $\boldsymbol{\Sigma}$ nhỏ nghĩa là mô hình tự tin: nó gần như chắc chắn hệ số $\boldsymbol{\beta}$ nằm quanh giá trị trung tâm, ít có khả năng lệch xa. Ngược lại, càng ít dữ liệu, $\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{Z}$ càng nhỏ, $\boldsymbol{\Sigma}$ càng lớn — mô hình còn mơ hồ, chưa dám chắc hệ số thật sự là bao nhiêu. Đây chính là lý do khoảng dự đoán ở mục 7 của tài liệu này thu hẹp dần qua mỗi lần huấn luyện lại: càng nhiều dữ liệu (kể cả dữ liệu dạng khoảng), $\boldsymbol{\Sigma}$ càng nhỏ, mô hình càng tự tin.

Có thể thấy công thức này hoạt động cụ thể ra sao ngay trong ví dụ ở mục 4.1 của tài liệu này. Ở đó, $\alpha=\lambda=1$, nên công thức rút gọn thành $\boldsymbol{\Sigma}=(\boldsymbol{I}+\boldsymbol{Z}_0^{\mathsf{T}}\boldsymbol{Z}_0)^{-1}$ — đúng bằng $\boldsymbol{A}_0^{-1}$ đã tính ở mục 4.2. Cụ thể, $\boldsymbol{Z}_0^{\mathsf{T}}\boldsymbol{Z}_0=\begin{bmatrix}4&0\\0&5\end{bmatrix}$ (lượng thông tin từ 5 quan sát hàng tháng), cộng $\boldsymbol{I}$ (phanh an toàn) thành $\boldsymbol{A}_0=\begin{bmatrix}5&0\\0&6\end{bmatrix}$, rồi nghịch đảo ra $\boldsymbol{\Sigma}=\boldsymbol{A}_0^{-1}=\begin{bmatrix}1/5&0\\0&1/6\end{bmatrix}$. Hai số trên đường chéo, $1/5$ và $1/6$, chính là độ không chắc chắn còn lại quanh hệ số góc $\beta_1$ và hằng số $\beta_0$ sau khi học từ 5 tháng dữ liệu đầu tiên. Ở mục 6.4, sau khi mô hình học thêm hai lần từ dữ liệu dạng khoảng, $\boldsymbol{\Sigma}_2$ có các số trên đường chéo nhỏ hơn ($12/63\approx0.19$ và $(16/3)/63\approx0.085$, so với $1/5=0.2$ và $1/6\approx0.167$ ban đầu) — đúng như trực giác đã nêu: nhiều dữ liệu hơn làm mô hình tự tin hơn, độ không chắc chắn giảm dần.

$$
\overline{\boldsymbol{\beta}}
=
\alpha\boldsymbol{\Sigma}
\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{y}.
$$

Vì trong ví dụ này $\alpha=\lambda=1$, hai công thức trên rút gọn được. Đặt

$$
\boldsymbol{A}
=
\boldsymbol{I}
+
\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{Z},
\qquad
\boldsymbol{b}
=
\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{y},
$$

thì

$$
\boldsymbol{\Sigma}=\boldsymbol{A}^{-1},
\qquad
\overline{\boldsymbol{\beta}}=\boldsymbol{A}^{-1}\boldsymbol{b}.
$$

Nói cách đơn giản: cứ mỗi lần có thêm dữ liệu mới, ta cộng dồn thông tin vào hai đại lượng $\boldsymbol{A}$ và $\boldsymbol{b}$, rồi giải một phép nghịch đảo ma trận để ra hệ số mới. Đây chính là phần việc lặp lại xuyên suốt toàn bộ ví dụ bên dưới.

## 4. Huấn luyện mô hình lần đầu bằng 5 quan sát hàng tháng

Số liệu ban đầu (tự đặt ra, không phải số liệu thật) như sau:

| Epoch | $x_k$ | Observed $\Delta d_k$ (mm) |
|---:|---:|---:|
| $k_1$ | $-1$ | $1$ |
| $k_2$ | $-1$ | $1$ |
| $k_3$ | $0$ | $-1$ |
| $k_4$ | $1$ | $-3$ |
| $k_5$ | $1$ | $-3$ |

Cần nhớ quy ước dấu trong ví dụ này: giá trị $\Delta d_k$ âm nghĩa là đất đang bị nén lún (compaction). Ví dụ tại $k_4$, giá trị $-3$ nghĩa là tháng đó lún 3 mm.

### 4.1 Xếp số liệu thành ma trận

Gộp 5 hàng $\boldsymbol{z}_k$ lại thành ma trận $\boldsymbol{Z}_0$, và 5 giá trị quan sát thành vector $\boldsymbol{y}_0$:

$$
\boldsymbol{Z}_0
=
\begin{bmatrix}
-1 & 1\\
-1 & 1\\
0 & 1\\
1 & 1\\
1 & 1
\end{bmatrix},
\qquad
\boldsymbol{y}_0
=
\begin{bmatrix}
1\\
1\\
-1\\
-3\\
-3
\end{bmatrix}.
$$

Mục 3 mới chỉ dùng $\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{Z}$ và $\boldsymbol{Z}^{\mathsf{T}}\boldsymbol{y}$ như một đại lượng cho sẵn, chưa chỉ ra cách tính ra từng con số. Phần này tính cụ thể cho $\boldsymbol{Z}_0$ ở trên.

Mỗi hàng của $\boldsymbol{Z}_0$ có dạng $\boldsymbol{z}_k = \begin{bmatrix}x_k & 1\end{bmatrix}$. Khi nhân $\boldsymbol{Z}_0^{\mathsf{T}}$ (ma trận $\boldsymbol{Z}_0$ lật ngang, kích thước $2\times5$) với $\boldsymbol{Z}_0$ (kích thước $5\times2$), mỗi phần tử của kết quả $2\times2$ chỉ là một phép cộng các tích theo cột — không cần công cụ nào ngoài cộng và nhân:

$$
\boldsymbol{Z}_0^{\mathsf{T}}\boldsymbol{Z}_0
=
\begin{bmatrix}
\sum_k x_k^2 & \sum_k x_k\\
\sum_k x_k & n
\end{bmatrix}.
$$

Thay 5 giá trị $x_k \in \{-1,-1,0,1,1\}$ vào:

- $\sum_k x_k^2 = (-1)^2+(-1)^2+0^2+1^2+1^2 = 1+1+0+1+1 = 4$ — đây chính là số 4 ở góc trên-trái.
- $\sum_k x_k = -1-1+0+1+1 = 0$ — đây là số 0 ở hai góc ngoài đường chéo.
- $n = 5$ (tổng số quan sát) — đây là số 5 ở góc dưới-phải.

Tương tự, $\boldsymbol{Z}_0^{\mathsf{T}}\boldsymbol{y}_0 = \begin{bmatrix}\sum_k x_k y_k\\ \sum_k y_k\end{bmatrix}$, với $y_k \in \{1,1,-1,-3,-3\}$:

- $\sum_k x_k y_k = (-1)(1)+(-1)(1)+(0)(-1)+(1)(-3)+(1)(-3) = -1-1+0-3-3 = -8$.
- $\sum_k y_k = 1+1-1-3-3 = -5$.

Vậy kết quả đầy đủ là:

$$
\boldsymbol{Z}_0^{\mathsf{T}}\boldsymbol{Z}_0
=
\begin{bmatrix}
4 & 0\\
0 & 5
\end{bmatrix},
\qquad
\boldsymbol{Z}_0^{\mathsf{T}}\boldsymbol{y}_0
=
\begin{bmatrix}
-8\\
-5
\end{bmatrix}.
$$

Cộng thêm ma trận đơn vị $\boldsymbol{I}$ (đại diện cho $\lambda=1$) vào góc trên, ta được hai đại lượng cộng dồn $\boldsymbol{A}_0$ và $\boldsymbol{b}_0$ — đây là "bộ nhớ" của mô hình sau lần huấn luyện đầu tiên:

$$
\boldsymbol{A}_0
=
\begin{bmatrix}
5 & 0\\
0 & 6
\end{bmatrix},
\qquad
\boldsymbol{b}_0
=
\begin{bmatrix}
-8\\
-5
\end{bmatrix}.
$$

### 4.2 Tính ra hệ số mô hình

Nghịch đảo $\boldsymbol{A}_0$ (dễ làm vì đây là ma trận đường chéo), rồi nhân với $\boldsymbol{b}_0$:

$$
\overline{\boldsymbol{\beta}}_0
=
\boldsymbol{A}_0^{-1}\boldsymbol{b}_0
=
\begin{bmatrix}
1/5 & 0\\
0 & 1/6
\end{bmatrix}
\begin{bmatrix}
-8\\
-5
\end{bmatrix}
=
\begin{bmatrix}
-1.600\\
-0.833
\end{bmatrix}.
$$

Vậy mô hình đầu tiên, học được từ 5 tháng dữ liệu, là:

$$
\widehat{\Delta d}_k
=
-1.600x_k-0.833.
$$

Đây là phương trình ta sẽ dùng ngay ở bước tiếp theo, để dự đoán ba tháng chưa có số liệu.

## 5. Chu kỳ thứ nhất: dự đoán, rồi cập nhật bằng một con số tổng

### 5.1 Dùng mô hình để ước tính ba tháng tiếp theo

Tại các mốc $k_6$, $k_7$, $k_8$, ta biết giá trị biến đầu vào $x_k$ (ví dụ: dữ liệu mực nước ngầm và biến dạng bề mặt vẫn đo được bình thường), nhưng **không có** số liệu MLCW thật của ba tháng này. Thay vào công thức mô hình vừa tìm được:

| Epoch | $x_k$ | Phép tính | Estimated $\widehat{\Delta d}_k$ (mm) |
|---:|---:|---:|---:|
| $k_6$ | $1$ | $-1.600(1)-0.833$ | $-2.433$ |
| $k_7$ | $0$ | $-1.600(0)-0.833$ | $-0.833$ |
| $k_8$ | $-1$ | $-1.600(-1)-0.833$ | $0.767$ |

Cộng ba giá trị ước tính này lại (dùng số chưa làm tròn để tránh sai số cộng dồn), ta được tổng ước tính của cả khoảng:

$$
\sum_{k\in I_1}\widehat{\Delta d}_k
=
-2.500\ \mathrm{mm}.
$$

Đây là con số mô hình **tự đoán**, chưa biết đúng sai. Bước tiếp theo là so nó với thực tế.

### 5.2 Nhận phép đo tổng thật từ hiện trường

Giả sử tại đầu khoảng, độ lún tích lũy (đo từ một mốc gốc nào đó) là:

$$
d_{\mathrm{start},1}=-5\ \mathrm{mm},
$$

và ba tháng sau, phép đo mới cho biết:

$$
d_{\mathrm{end},1}=-8\ \mathrm{mm}.
$$

Lấy hiệu hai con số này, ta biết tổng độ lún thật sự đã xảy ra trong ba tháng đó:

$$
\Delta d_{I_1}
=
d_{\mathrm{end},1}-d_{\mathrm{start},1}
=
-8-(-5)
=
-3\ \mathrm{mm}.
$$

Cần nhấn mạnh: phép đo này **chỉ cho biết tổng của ba tháng**. Nó không cho biết riêng tháng nào lún nhiều, tháng nào lún ít.

(Chỉ để kiểm tra lại ví dụ — không phải điều mô hình được biết: nếu ta biết trước giá trị thật của từng tháng là $-3$, $-1$, $1$ mm, cộng lại đúng bằng $-3$ mm. Ba con số này được giữ riêng để so sánh sai số về sau, nhưng **không** được đưa vào tập huấn luyện.)

### 5.3 Biến phép đo tổng thành một hàng dữ liệu mới

Đây là bước cốt lõi của toàn bộ thuật toán: làm sao dùng một con số tổng (không biết chi tiết từng tháng) để huấn luyện lại mô hình một cách đúng đắn.

Khoảng thứ nhất có độ dài 3 tháng, ký hiệu $H_{I_1}=3$. Cộng ba giá trị $x_k$ của ba tháng trong khoảng:

$$
\sum_{k\in I_1}x_k
=
1+0-1
=
0.
$$

Ý tưởng là: mỗi tháng trong khoảng $I_1$ vẫn có một phương trình mô hình riêng. Ba tháng $k_6$, $k_7$, và $k_8$ có thể được viết ra đầy đủ như sau:

$$
\begin{aligned}
\Delta d_{6} &= \beta_1 x_6+\beta_0+\varepsilon_6,\\
\Delta d_{7} &= \beta_1 x_7+\beta_0+\varepsilon_7,\\
\Delta d_{8} &= \beta_1 x_8+\beta_0+\varepsilon_8.
\end{aligned}
$$

Nếu cộng cả ba dòng này lại, vế trái trở thành tổng độ lún của cả khoảng:

$$
\Delta d_{6}+\Delta d_{7}+\Delta d_{8}
=
\Delta d_{I_1}.
$$

Vế phải cũng được cộng theo đúng từng thành phần. Các phần chứa $\beta_1$ gộp lại thành $\beta_1(x_6+x_7+x_8)$. Ba hằng số $\beta_0$ gộp lại thành $3\beta_0$. Ba phần sai số gộp lại thành $\varepsilon_6+\varepsilon_7+\varepsilon_8$. Vì vậy:

$$
\Delta d_{I_1}
=
\beta_1(x_6+x_7+x_8)
+
3\beta_0
+
(\varepsilon_6+\varepsilon_7+\varepsilon_8).
$$

Với ký hiệu tổng quát, $x_6+x_7+x_8$ chính là $\sum_{k\in I_1}x_k$, số tháng trong khoảng là $H_{I_1}=3$, và phần sai số cộng dồn được viết là $\varepsilon_{I_1}$. Khi đó phương trình trên trở thành:

$$
\Delta d_{I_1}
=
\beta_1
\sum_{k\in I_1}x_k
+
H_{I_1}\beta_0
+
\varepsilon_{I_1}.
$$

Trong ví dụ này, tổng $x_k$ của khoảng thứ nhất bằng 0, số tháng bằng 3, và tổng độ lún thật bằng $-3$ mm. Do đó phương trình của khoảng thứ nhất có dạng:

$$
-3
=
\beta_1(0)
+
3\beta_0
+
\varepsilon_{I_1}.
$$

Nếu viết phương trình này dưới dạng một hàng dữ liệu để đưa vào mô hình, hệ số đi cùng $\beta_1$ là 0, hệ số đi cùng $\beta_0$ là 3, và giá trị quan sát là $-3$. Từ đó, ta có một hàng dữ liệu thô mới:

$$
\begin{bmatrix}
0 & 3
\end{bmatrix},
\qquad
-3.
$$

Nhưng hàng này chưa dùng ngay được. Lý do: độ nhiễu (variance) của một tổng 3 tháng độc lập lớn gấp 3 lần độ nhiễu của một tháng đơn lẻ — đây là quy tắc thống kê cơ bản khi cộng các đại lượng ngẫu nhiên độc lập. Nếu đưa thẳng hàng này vào huấn luyện chung với các hàng tháng, mô hình sẽ hiểu nhầm rằng đây là một quan sát chắc chắn ngang bằng một tháng, trong khi thực ra nó nhiễu hơn nhiều. Để sửa việc này, ta chia cả hàng và giá trị quan sát cho $\sqrt{3}$ (căn bậc hai của số tháng), đưa mức nhiễu về đúng thang với các hàng tháng:

$$
\boldsymbol{z}_{I_1}
=
\begin{bmatrix}
0 & \sqrt{3}
\end{bmatrix},
\qquad
y_{I_1}^{\mathrm{scaled}}
=
-\sqrt{3}.
$$

Một điều cần làm rõ: phép chia này **không** biến một quan sát thành ba quan sát giả. Sau khi chia, đây vẫn chỉ là **một hàng dữ liệu duy nhất** — chỉ là đã được cân chỉnh đúng thang nhiễu, để khi ghép chung với 5 hàng tháng ban đầu, mô hình không bị đánh lừa.

### 5.4 Huấn luyện lại mô hình với hàng dữ liệu mới này

Hàng mới đóng góp thêm vào hai đại lượng cộng dồn. Để thấy từng số đến từ đâu, viết hàng dữ liệu mới dưới dạng cột:

$$
\boldsymbol{z}_{I_1}^{\mathsf{T}}
=
\begin{bmatrix}
0\\
\sqrt{3}
\end{bmatrix}.
$$

Khi nhân $\boldsymbol{z}_{I_1}^{\mathsf{T}}$ với $\boldsymbol{z}_{I_1}$, từng phần tử của ma trận được tính như sau:

$$
\boldsymbol{z}_{I_1}^{\mathsf{T}}
\boldsymbol{z}_{I_1}
=
\begin{bmatrix}
0\\
\sqrt{3}
\end{bmatrix}
\begin{bmatrix}
0 & \sqrt{3}
\end{bmatrix}
=
\begin{bmatrix}
0\cdot0 & 0\cdot\sqrt{3}\\
\sqrt{3}\cdot0 & \sqrt{3}\cdot\sqrt{3}
\end{bmatrix}.
$$

Vì vậy:

$$
\boldsymbol{z}_{I_1}^{\mathsf{T}}
\boldsymbol{z}_{I_1}
=
\begin{bmatrix}
0 & 0\\
0 & 3
\end{bmatrix}.
$$

Vector bên phải cũng được tính trực tiếp từ hàng dữ liệu mới:

$$
\boldsymbol{z}_{I_1}^{\mathsf{T}}
y_{I_1}^{\mathrm{scaled}}
=
\begin{bmatrix}
0\\
\sqrt{3}
\end{bmatrix}
(-\sqrt{3})
=
\begin{bmatrix}
0\\
-3
\end{bmatrix}.
$$

Cộng vào $\boldsymbol{A}_0$ và $\boldsymbol{b}_0$ đã có từ lần huấn luyện đầu, ta được bộ nhớ mới:

$$
\boldsymbol{A}_1
=
\boldsymbol{A}_0
+
\boldsymbol{z}_{I_1}^{\mathsf{T}}\boldsymbol{z}_{I_1}
=
\begin{bmatrix}
5 & 0\\
0 & 9
\end{bmatrix},
\qquad
\boldsymbol{b}_1
=
\boldsymbol{b}_0
+
\boldsymbol{z}_{I_1}^{\mathsf{T}}y_{I_1}^{\mathrm{scaled}}
=
\begin{bmatrix}
-8\\
-8
\end{bmatrix}.
$$

Giải lại như bước 4.2:

$$
\overline{\boldsymbol{\beta}}_1
=
\boldsymbol{A}_1^{-1}\boldsymbol{b}_1
=
\begin{bmatrix}
-1.600\\
-0.889
\end{bmatrix}.
$$

Mô hình sau khi cập nhật lần một:

$$
\widehat{\Delta d}_k
=
-1.600x_k-0.889.
$$

Chú ý: chỉ có hằng số $\beta_0$ thay đổi (từ $-0.833$ thành $-0.889$), còn hệ số góc $\beta_1$ không đổi. Đây không phải một quy luật chung của thuật toán — nó chỉ xảy ra vì trong bộ số liệu ví dụ này, tổng $x_k$ của khoảng $I_1$ tình cờ bằng 0, nên hàng dữ liệu mới không mang thông tin gì về hệ số góc.

## 6. Chu kỳ thứ hai: lặp lại quy trình

### 6.1 Ước tính ba tháng kế tiếp bằng mô hình vừa cập nhật

| Epoch | $x_k$ | Phép tính | Estimated $\widehat{\Delta d}_k$ (mm) |
|---:|---:|---:|---:|
| $k_9$ | $-1$ | $-1.600(-1)-0.889$ | $0.711$ |
| $k_{10}$ | $1$ | $-1.600(1)-0.889$ | $-2.489$ |
| $k_{11}$ | $1$ | $-1.600(1)-0.889$ | $-2.489$ |

Tổng ước tính của khoảng thứ hai:

$$
\sum_{k\in I_2}\widehat{\Delta d}_k
=
0.711-2.489-2.489
=
-4.267\ \mathrm{mm}.
$$

### 6.2 Nhận phép đo tổng thứ hai

Điểm cuối của khoảng trước trở thành điểm đầu của khoảng mới:

$$
d_{\mathrm{start},2}
=
d_{\mathrm{end},1}
=
-8\ \mathrm{mm}.
$$

Giả sử phép đo mới ở cuối khoảng thứ hai là:

$$
d_{\mathrm{end},2}=-12\ \mathrm{mm}.
$$

Vậy tổng độ lún thật của khoảng thứ hai:

$$
\Delta d_{I_2}
=
-12-(-8)
=
-4\ \mathrm{mm}.
$$

(Để kiểm tra lại ví dụ: nếu biết trước ba giá trị tháng thật là $1$, $-3$, $-2$ mm, cộng lại đúng bằng $-4$ mm — nhưng như trước, ba con số này không được đưa vào huấn luyện.)

### 6.3 Tạo hàng dữ liệu thứ hai

Làm đúng các bước như mục 5.3. Độ dài khoảng vẫn là $H_{I_2}=3$. Tổng $x_k$ của khoảng này:

$$
\sum_{k\in I_2}x_k
=
-1+1+1
=
1.
$$

Ba tháng trong khoảng $I_2$ cũng có ba phương trình riêng:

$$
\begin{aligned}
\Delta d_{9} &= \beta_1 x_9+\beta_0+\varepsilon_9,\\
\Delta d_{10} &= \beta_1 x_{10}+\beta_0+\varepsilon_{10},\\
\Delta d_{11} &= \beta_1 x_{11}+\beta_0+\varepsilon_{11}.
\end{aligned}
$$

Cộng ba phương trình này lại:

$$
\Delta d_{I_2}
=
\beta_1(x_9+x_{10}+x_{11})
+
3\beta_0
+
(\varepsilon_9+\varepsilon_{10}+\varepsilon_{11}).
$$

Trong ví dụ này, $x_9+x_{10}+x_{11}=1$ và tổng độ lún thật của khoảng thứ hai bằng $-4$ mm. Vì vậy:

$$
-4
=
\beta_1(1)
+
3\beta_0
+
\varepsilon_{I_2}.
$$

Do đó, hàng dữ liệu thô là:

$$
\begin{bmatrix}
1 & 3
\end{bmatrix},
\qquad
-4.
$$

Chia cho $\sqrt{3}$:

$$
\boldsymbol{z}_{I_2}
=
\begin{bmatrix}
1/\sqrt{3} & \sqrt{3}
\end{bmatrix},
\qquad
y_{I_2}^{\mathrm{scaled}}
=
-4/\sqrt{3}.
$$

Đóng góp thêm vào hai đại lượng cộng dồn. Cách tính giống hệt chu kỳ thứ nhất, nhưng lần này tổng $x_k$ bằng 1, nên hàng mới có thông tin về cả $\beta_1$ và $\beta_0$:

$$
\boldsymbol{z}_{I_2}^{\mathsf{T}}
=
\begin{bmatrix}
1/\sqrt{3}\\
\sqrt{3}
\end{bmatrix}.
$$

Do đó:

$$
\boldsymbol{z}_{I_2}^{\mathsf{T}}
\boldsymbol{z}_{I_2}
=
\begin{bmatrix}
1/\sqrt{3}\\
\sqrt{3}
\end{bmatrix}
\begin{bmatrix}
1/\sqrt{3} & \sqrt{3}
\end{bmatrix}
=
\begin{bmatrix}
(1/\sqrt{3})(1/\sqrt{3}) & (1/\sqrt{3})\sqrt{3}\\
\sqrt{3}(1/\sqrt{3}) & \sqrt{3}\sqrt{3}
\end{bmatrix}.
$$

Rút gọn từng phần tử, ta được:

$$
\boldsymbol{z}_{I_2}^{\mathsf{T}}
\boldsymbol{z}_{I_2}
=
\begin{bmatrix}
1/3 & 1\\
1 & 3
\end{bmatrix}.
$$

Vector bên phải được tính từ cùng hàng dữ liệu:

$$
\boldsymbol{z}_{I_2}^{\mathsf{T}}
y_{I_2}^{\mathrm{scaled}}
=
\begin{bmatrix}
1/\sqrt{3}\\
\sqrt{3}
\end{bmatrix}
(-4/\sqrt{3})
=
\begin{bmatrix}
-4/3\\
-4
\end{bmatrix}.
$$

### 6.4 Huấn luyện lại mô hình lần thứ hai

Lúc này, tập dữ liệu huấn luyện gồm ba phần: 5 quan sát hàng tháng ban đầu, cộng với hàng ràng buộc của khoảng $I_1$, cộng với hàng ràng buộc của khoảng $I_2$. Cộng dồn tiếp vào $\boldsymbol{A}_1$ và $\boldsymbol{b}_1$:

$$
\boldsymbol{A}_2
=
\boldsymbol{A}_1
+
\boldsymbol{z}_{I_2}^{\mathsf{T}}\boldsymbol{z}_{I_2}
=
\begin{bmatrix}
16/3 & 1\\
1 & 12
\end{bmatrix},
\qquad
\boldsymbol{b}_2
=
\boldsymbol{b}_1
+
\boldsymbol{z}_{I_2}^{\mathsf{T}}y_{I_2}^{\mathrm{scaled}}
=
\begin{bmatrix}
-28/3\\
-12
\end{bmatrix}.
$$

Các phần tử trong $\boldsymbol{A}_2$ và $\boldsymbol{b}_2$ chỉ là kết quả cộng trực tiếp:

$$
\begin{bmatrix}
5 & 0\\
0 & 9
\end{bmatrix}
+
\begin{bmatrix}
1/3 & 1\\
1 & 3
\end{bmatrix}
=
\begin{bmatrix}
16/3 & 1\\
1 & 12
\end{bmatrix},
\qquad
\begin{bmatrix}
-8\\
-8
\end{bmatrix}
+
\begin{bmatrix}
-4/3\\
-4
\end{bmatrix}
=
\begin{bmatrix}
-28/3\\
-12
\end{bmatrix}.
$$

Lần này $\boldsymbol{A}_2$ không còn là ma trận đường chéo nữa (vì có số $1$ ở ngoài đường chéo), nên phép nghịch đảo phức tạp hơn một chút:

$$
\boldsymbol{A}_2^{-1}
=
\frac{1}{63}
\begin{bmatrix}
12 & -1\\
-1 & 16/3
\end{bmatrix}.
$$

Nhân ra, ta được hệ số mô hình sau hai lần cập nhật:

$$
\overline{\boldsymbol{\beta}}_2
=
\boldsymbol{A}_2^{-1}\boldsymbol{b}_2
=
\frac{1}{63}
\begin{bmatrix}
12 & -1\\
-1 & 16/3
\end{bmatrix}
\begin{bmatrix}
-28/3\\
-12
\end{bmatrix}
=
\begin{bmatrix}
-100/63\\
-164/189
\end{bmatrix}
\approx
\begin{bmatrix}
-1.587\\
-0.868
\end{bmatrix}.
$$

Mô hình sẵn sàng cho khoảng kế tiếp là:

$$
\widehat{\Delta d}_k
=
-1.587x_k-0.868.
$$

Ví dụ: nếu biến đầu vào của tháng kế tiếp bằng 0 ($x_{12}=0$), điểm dự đoán trung tâm sẽ là:

$$
\widehat{\Delta d}_{12}
=
-1.587(0)-0.868
=
-0.868\ \mathrm{mm}.
$$

## 7. Tính khoảng dự đoán 90% bằng tay

Mô hình không chỉ cho một con số dự đoán duy nhất — nó còn cho biết mức độ không chắc chắn quanh con số đó, dưới dạng một khoảng dự đoán (posterior predictive interval). Phần này tính khoảng đó bằng tay, tiếp nối ngay sau bước 6.4.

Từ lần cập nhật thứ hai, ta đã có:

$$
\boldsymbol{\Sigma}_2
=
\boldsymbol{A}_2^{-1}
=
\frac{1}{63}
\begin{bmatrix}
12 & -1\\
-1 & 16/3
\end{bmatrix}.
$$

Tại $x_{12}=0$, hàng dữ liệu dùng để dự đoán là:

$$
\boldsymbol{z}_{12}
=
\begin{bmatrix}
0 & 1
\end{bmatrix}.
$$

Độ không chắc chắn của một dự đoán gồm hai phần cộng lại: phần nhiễu vốn có của dữ liệu (đo bằng $\alpha^{-1}$), và phần không chắc chắn về chính hệ số mô hình (đo bằng $\boldsymbol{z}_{12}\boldsymbol{\Sigma}_2\boldsymbol{z}_{12}^{\mathsf{T}}$). Cộng hai phần này lại, với $\alpha=1$:

$$
\boldsymbol{z}_{12}
\boldsymbol{\Sigma}_2
\boldsymbol{z}_{12}^{\mathsf{T}}
=
\begin{bmatrix}
0 & 1
\end{bmatrix}
\left(
\frac{1}{63}
\begin{bmatrix}
12 & -1\\
-1 & 16/3
\end{bmatrix}
\right)
\begin{bmatrix}
0\\
1
\end{bmatrix}
=
\frac{16}{189}.
$$

$$
\sigma_{12}^{2}
=
\alpha^{-1}
+
\boldsymbol{z}_{12}
\boldsymbol{\Sigma}_2
\boldsymbol{z}_{12}^{\mathsf{T}}
=
1+
\frac{16}{189}
=
1.0847.
$$

Lấy căn bậc hai để ra độ lệch chuẩn:

$$
\sigma_{12}
=
\sqrt{1.0847}
=
1.0415\ \mathrm{mm}.
$$

Khoảng dự đoán 90% (nominal 90% posterior predictive interval) được tính bằng cách lấy điểm dự đoán trung tâm, cộng trừ 1.645 lần độ lệch chuẩn — con số 1.645 là hệ số chuẩn ứng với mức tin cậy 90% của phân bố chuẩn:

$$
\widehat{\Delta d}_{12}
\pm
1.645\sigma_{12}.
$$

Khoảng cách từ điểm trung tâm đến mỗi biên:

$$
1.645(1.0415)
=
1.713\ \mathrm{mm}.
$$

Vậy khoảng dự đoán cuối cùng là:

$$
\left[
-0.868-1.713,
-0.868+1.713
\right]
=
\left[
-2.581,
0.845
\right]\ \mathrm{mm}.
$$

Cần nói rõ đây là loại khoảng gì, vì có nhiều loại khoảng dễ gây nhầm lẫn: đây là khoảng dự đoán hậu nghiệm (posterior predictive interval) cho **một giá trị độ lún hàng tháng cụ thể**. Nó **không phải** khoảng tin cậy (confidence interval) của giá trị trung bình hồi quy, và cũng **không phải** khoảng conformal prediction — hai loại khoảng dùng nguyên lý tính toán khác hẳn.

## 8. Tóm tắt thuật toán tổng quát

Toàn bộ ví dụ ở trên chỉ là một trường hợp cụ thể của quy trình chung sau đây, áp dụng được cho bất kỳ khoảng thời gian nào và bất kỳ số lượng biến đầu vào nào:

1. Huấn luyện mô hình Bayesian ridge regression bằng các quan sát MLCW hàng tháng trong giai đoạn hiệu chỉnh ban đầu (initial calibration period).
2. Ước tính từng giá trị độ lún hàng tháng trong khoảng kế tiếp, dùng dữ liệu mực nước ngầm (GWL) và biến dạng bề mặt (cGNSS) hàng tháng — hai loại dữ liệu này vẫn đo được đều đặn, không bị gián đoạn.
3. **Không** đưa các giá trị MLCW hàng tháng thật (nhưng bị ẩn, chưa biết) của khoảng đó vào việc huấn luyện mô hình.
4. Tại điểm cuối khoảng, tính độ lún tổng của cả khoảng, bằng hiệu của hai phép đo tích lũy liên tiếp.
5. Cộng các hàng dữ liệu đầu vào (đã chuẩn hóa) của tất cả các tháng trong khoảng lại với nhau.
6. Tạo ra một hàng dữ liệu mới đại diện cho cả khoảng, trong đó phần đóng góp của hằng số $\beta_0$ bằng đúng số tháng $H_I$ trong khoảng.
7. Chia cả hàng dữ liệu và giá trị quan sát cho $\sqrt{H_I}$, để đưa mức nhiễu về đúng thang với các hàng tháng.
8. Huấn luyện lại toàn bộ mô hình Bayesian ridge, dùng tất cả các hàng tháng ban đầu cộng với tất cả các hàng khoảng đã nhận được từ trước đến nay.
9. Dùng mô hình vừa huấn luyện lại để dự đoán cho khoảng tiếp theo.

Sơ đồ dưới đây tóm tắt trình tự của ví dụ hai chu kỳ đã trình bày ở trên:

```text
Monthly rows k1-k5
        |
        v
Fit model 0
        |
        v
Estimate k6-k8
        |
        v
Receive cumulative constraint I1
        |
        v
Refit using k1-k5 + I1
        |
        v
Estimate k9-k11
        |
        v
Receive cumulative constraint I2
        |
        v
Refit using k1-k5 + I1 + I2
```

## 9. Trả lời trước các câu hỏi người đọc thường thắc mắc

### 9.1 Con số đo tổng có được chia đều ra cho từng tháng trong khoảng không?

Không. Thuật toán **không** lấy $\Delta d_I/H_I$ rồi gán làm giá trị giả định cho mỗi tháng. Một phép đo tổng ở điểm cuối khoảng chỉ tạo ra **đúng một** hàng ràng buộc (interval constraint) duy nhất trong tập huấn luyện. Vai trò của các biến đầu vào hàng tháng (GWL, cGNSS) là giúp mô hình ước tính cách độ lún phân bố theo thời gian bên trong khoảng đó; còn phép đo tổng chỉ ràng buộc **tổng** của cả khoảng, không ràng buộc riêng từng tháng.

### 9.2 Các giá trị MLCW hàng tháng bị ẩn có được dùng để cập nhật mô hình không?

Không. Trong ví dụ ở mục 5 và 6, các giá trị hàng tháng thật (ví dụ $-3$, $-1$, $1$ mm ở khoảng thứ nhất) chỉ được giữ lại để **đánh giá hồi cứu** — tức là dùng sau này để kiểm tra mô hình dự đoán đúng sai đến đâu. Tập dữ liệu dùng để huấn luyện lại mô hình, sau mỗi lần nhận phép đo tổng, chỉ nhận thêm đúng một hàng ràng buộc theo khoảng, không bao giờ nhận thêm các giá trị hàng tháng bị ẩn đó.

### 9.3 Vì sao phải cộng tất cả biến đầu vào của cả khoảng lại, thay vì chỉ dùng giá trị tại điểm cuối?

Vì phép đo tổng là **tổng** của các phản ứng (response) hàng tháng cộng lại. Khi cộng các phương trình hồi quy của từng tháng lại với nhau (như đã làm ở mục 5.3), phần đóng góp của biến đầu vào cũng phải là **tổng** của các hàng đầu vào hàng tháng — để hai vế của phương trình khớp nhau về mặt toán học. Giá trị biến đầu vào riêng tại điểm cuối khoảng không đại diện cho toàn bộ điều kiện thủy văn và biến dạng bề mặt đã xảy ra trong suốt cả khoảng thời gian đó.

### 9.4 Vì sao phải chia cho $\sqrt{H_I}$?

Mô hình giả định rằng phần nhiễu (residual) của các tháng độc lập với nhau. Khi cộng $H_I$ phần nhiễu độc lập lại, độ nhiễu (variance) của tổng sẽ lớn gấp $H_I$ lần độ nhiễu của một tháng đơn lẻ — đây là một quy tắc thống kê cơ bản, không phải giả định riêng của bài toán này. Chia toàn bộ phương trình của khoảng cho $\sqrt{H_I}$ sẽ đưa mức nhiễu của hàng khoảng về đúng thang với các hàng tháng, để mô hình không đánh giá sai mức độ tin cậy giữa hai loại hàng dữ liệu. Phép chia này chỉ là một phép biến đổi toán học hợp lệ (không làm thay đổi tính đúng đắn của đẳng thức), và quan trọng là nó **không** tạo ra thêm quan sát nào — trước và sau khi chia vẫn chỉ là một hàng dữ liệu.

### 9.5 "Cập nhật" ở đây có phải là một phép cập nhật hậu nghiệm tuần tự (sequential Bayesian posterior update) theo đúng nghĩa toán học không?

Không hẳn theo nghĩa tính toán tuần tự thuần túy. Quy trình xử lý thật **huấn luyện lại toàn bộ mô hình Bayesian ridge từ đầu** tại mỗi điểm cuối khoảng, chứ không cập nhật dần từng bước nhỏ. Tập dữ liệu huấn luyện luôn bao gồm đầy đủ các hàng tháng ban đầu, cộng với tất cả các hàng ràng buộc theo khoảng đã nhận được từ trước đến thời điểm đó. Việc huấn luyện lại toàn bộ (full refit) như vậy cho phép mô hình ước lượng lại cả phân bố hệ số, cả độ chính xác của nhiễu ($\alpha$), cả mức độ co hệ số ($\lambda$) — dựa trên toàn bộ thông tin đang có, không chỉ dựa trên bước cập nhật gần nhất.

### 9.6 Vì sao ví dụ này cố định $\alpha$ và $\lambda$ thay vì để mô hình tự ước lượng như thật?

Chỉ để phép tính ma trận có thể làm bằng tay được. Trong quy trình xử lý thật, hai tham số này được ước lượng lại từ chính dữ liệu (bằng phương pháp marginal likelihood) mỗi lần mô hình huấn luyện lại — không cố định như ở đây. Nhưng cách tạo hàng dữ liệu theo khoảng, cách chia tỷ lệ theo $\sqrt{H_I}$, và việc huấn luyện lại toàn bộ mô hình — ba điều cốt lõi của thuật toán — hoàn toàn không thay đổi dù $\alpha$ và $\lambda$ có cố định hay không.

## 10. Một giả định cần nói thẳng ra, không giấu

Phép chia cho $\sqrt{H_I}$ dựa trên một giả định cụ thể: các phần nhiễu hàng tháng (monthly residuals) độc lập với nhau, có giá trị trung bình bằng không, và có độ nhiễu không đổi theo thời gian trong cùng một lớp đất. Đây là một giả định làm việc (working assumption) của khung thống kê được chọn để dùng — nó **không phải** một định luật vật lý bắt buộc đúng của hệ thống tầng chứa nước (aquifer system).

Trên thực tế, nếu phần nhiễu giữa các tháng có tương quan với nhau theo thời gian (temporal dependence), hoặc nếu mối quan hệ giữa biến đầu vào và độ lún thay đổi theo thời gian, thì mức độ không chắc chắn thật sự có thể khác với mức độ mô hình tính ra. Vì vậy, phần Methods của bản thảo cần nói rõ giả định này đã được dùng, và ảnh hưởng của giả định này nên được bàn đến như một giới hạn (limitation) của phương pháp, chứ không nên coi là điều hiển nhiên đúng.
