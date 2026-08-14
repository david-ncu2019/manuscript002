# Giải thích các phép tính trong Methods 3.4.2

**Thời gian ghi chú:** 2026/08/10 00:50:36  
**File được giải thích:** `sections/methods005.tex`  
**Tiểu mục:** `Reduced measurement frequency`

## Mục đích của thí nghiệm

Thí nghiệm này mô phỏng một lịch quan trắc trong đó mực nước dưới đất và chuyển vị thẳng đứng bề mặt vẫn được ghi nhận hằng tháng, nhưng MLCW chỉ cung cấp một quan trắc biến dạng tích lũy sau mỗi khoảng đo. Mô hình vẫn ước tính gia số biến dạng của từng tháng. Các giá trị MLCW hằng tháng bên trong khoảng đo được che khỏi quá trình hiệu chỉnh và cập nhật mô hình. Chúng chỉ được giữ lại để đánh giá hồi cứu sau khi mô hình đã tạo dự đoán.

## Bước 1. Hiệu chỉnh mô hình từ số liệu hằng tháng ban đầu

Mỗi kịch bản bắt đầu bằng một chuỗi MLCW hằng tháng liên tục. Các quan trắc này được dùng để xác định quan hệ giữa gia số biến dạng MLCW và các biến đầu vào hằng tháng. Với depth section $s$ và tháng $t$, mô hình Bayesian ridge regression có dạng tổng quát

$$
y_{s,t}=\beta_{0,s}+\boldsymbol{x}_{s,t}^{\mathsf T}\boldsymbol{\beta}_s+\varepsilon_{s,t}.
$$

Trong đó, $y_{s,t}$ là gia số biến dạng MLCW quan trắc được, $\boldsymbol{x}_{s,t}$ là vector các biến đầu vào đã chuẩn hóa, $\beta_{0,s}$ là hệ số chặn, $\boldsymbol{\beta}_s$ là các hệ số hồi quy, và $\varepsilon_{s,t}$ là phần sai khác chưa được mô hình giải thích.

## Bước 2. Ước tính các tháng trong khoảng giảm tần suất đo MLCW

Sau giai đoạn hiệu chỉnh ban đầu, mô hình đi vào một khoảng gồm $H_I$ tháng. Trong khoảng này, các biến đầu vào hằng tháng vẫn có sẵn nên mô hình tạo một ước tính $\widehat{y}_{s,t}$ cho từng tháng. Tuy nhiên, các giá trị MLCW hằng tháng thực tế không được dùng để điều chỉnh mô hình giữa khoảng.

Ở cuối khoảng $I$, quan trắc MLCW cung cấp tổng biến dạng tích lũy trong toàn khoảng

$$
Y_{s,I}=\sum_{t\in I}y_{s,t}.
$$

Quan trắc này chỉ cho biết tổng biến dạng của cả khoảng. Nó không cho biết tổng biến dạng đó được phân bố như thế nào giữa các tháng.

## Bước 3. Biểu diễn quan trắc tích lũy trong mô hình hằng tháng

Cộng phương trình hồi quy của tất cả các tháng trong khoảng $I$ cho kết quả

$$
Y_{s,I}
=
H_I\beta_{0,s}
+
\left(\sum_{t\in I}\boldsymbol{x}_{s,t}\right)^{\mathsf T}\boldsymbol{\beta}_s
+
\varepsilon_{s,I}.
$$

Hệ số chặn trở thành $H_I\beta_{0,s}$ vì cùng một hệ số chặn xuất hiện trong mỗi tháng. Các biến đầu vào đã chuẩn hóa được cộng theo tháng. Phần dư tích lũy là

$$
\varepsilon_{s,I}=\sum_{t\in I}\varepsilon_{s,t}.
$$

Việc cộng các phương trình không tạo ra các quan trắc MLCW hằng tháng mới. Nó chỉ chuyển một quan trắc tổng cộng thành một ràng buộc phù hợp với mô hình đang hoạt động ở quy mô tháng.

## Bước 4. Vì sao phải chia phương trình tích lũy cho $\sqrt{H_I}$

Mô hình giả định phần dư hằng tháng có phương sai $\alpha_s^{-1}$. Nếu các phần dư hằng tháng độc lập theo giả định của mô hình, phương sai của tổng $H_I$ phần dư là

$$
\operatorname{Var}(\varepsilon_{s,I})=H_I\alpha_s^{-1}.
$$

Vì vậy, phương trình tích lũy có mức biến động của phần dư lớn hơn phương trình hằng tháng. Để quan trắc hằng tháng và quan trắc tích lũy có cùng thang phương sai khi cùng được đưa vào hồi quy, toàn bộ phương trình tích lũy được chia cho $\sqrt{H_I}$

$$
\frac{Y_{s,I}}{\sqrt{H_I}}
=
\sqrt{H_I}\,\beta_{0,s}
+
\left(
\frac{1}{\sqrt{H_I}}
\sum_{t\in I}\boldsymbol{x}_{s,t}
\right)^{\mathsf T}\boldsymbol{\beta}_s
+
\widetilde{\varepsilon}_{s,I}.
$$

Khi đó,

$$
\widetilde{\varepsilon}_{s,I}
=
\frac{\varepsilon_{s,I}}{\sqrt{H_I}},
\qquad
\operatorname{Var}(\widetilde{\varepsilon}_{s,I})
=
\alpha_s^{-1}.
$$

Phép chia này không chia quan trắc tích lũy thành các giá trị MLCW hằng tháng. Nó chỉ thay đổi trọng số toán học của phương trình tích lũy để phương trình này có thể được kết hợp nhất quán với các phương trình hằng tháng ban đầu.

## Bước 5. Cập nhật mô hình sau mỗi khoảng đo

Chu trình được thực hiện theo thứ tự sau.

1. Hiệu chỉnh mô hình bằng các quan trắc MLCW hằng tháng ban đầu và các quan trắc tích lũy đã nhận được từ những khoảng trước.
2. Dùng GWL và cGNSS hằng tháng để ước tính gia số biến dạng trong khoảng kế tiếp.
3. Không sử dụng các giá trị MLCW hằng tháng bị che trong khoảng đó để hiệu chỉnh hoặc cập nhật mô hình.
4. Khi quan trắc tích lũy cuối khoảng có sẵn, chuyển nó thành phương trình đã chia cho $\sqrt{H_I}$.
5. Thêm phương trình tích lũy này vào tập hiệu chỉnh và hiệu chỉnh lại mô hình trước khoảng tiếp theo.

Do đó, dữ liệu hiệu chỉnh ở các chu trình sau gồm hai loại thông tin. Loại thứ nhất là các quan trắc MLCW hằng tháng từ giai đoạn lịch sử ban đầu. Loại thứ hai là các quan trắc MLCW tích lũy từ những khoảng đo đã hoàn thành. Các giá trị MLCW hằng tháng nằm bên trong những khoảng giảm tần suất không bao giờ được đưa trở lại quá trình hiệu chỉnh.

## Bước 6. Đánh giá ở quy mô tháng

Sau khi dự đoán, giá trị MLCW hằng tháng đã được giữ riêng được dùng làm dữ liệu tham chiếu. Sai số của tháng $t$ là

$$
e_{s,t}=\widehat{y}_{s,t}-y_{s,t}.
$$

Các sai số này cho biết mô hình phân bố tổng biến dạng giữa các tháng tốt đến mức nào. MAE, RMSE và mean signed error được tính từ các sai số hằng tháng cho từng depth section và cho tất cả các section gộp lại.

## Bước 7. Đánh giá ở cuối khoảng đo

Tổng các ước tính hằng tháng được so sánh với quan trắc tích lũy ở cuối khoảng

$$
e_{s,I}
=
\sum_{t\in I}\widehat{y}_{s,t}-Y_{s,I}.
$$

Sai số này cho biết tổng biến dạng ước tính của cả khoảng có phù hợp với quan trắc tích lũy hay không. Một endpoint error nhỏ không bảo đảm rằng mọi ước tính hằng tháng đều chính xác, vì sai số dương và sai số âm giữa các tháng có thể triệt tiêu nhau. Vì vậy, kết quả phải được xem ở cả quy mô tháng và quy mô khoảng đo.

## Cách hiểu toàn bộ quy trình

Mô hình không tái tạo các giá trị MLCW hằng tháng từ một phép chia đơn giản của tổng tích lũy. GWL và cGNSS hằng tháng cung cấp thông tin để mô hình phân bố biến dạng theo thời gian. Quan trắc MLCW tích lũy chỉ ràng buộc tổng biến dạng trong mỗi khoảng và được dùng để hiệu chỉnh lại mô hình cho chu trình kế tiếp. Thiết kế này kiểm tra liệu mô hình còn có thể ước tính biến dạng hằng tháng khi tần suất đo MLCW giảm nhưng các dữ liệu quan trắc bổ trợ vẫn tiếp tục có sẵn hay không.

## Câu hỏi bổ sung và giải thích

**Thời gian:** 2026/08/10 01:05:55

### Câu hỏi

> Có phải là, thay vì ta phải lần ngược lại số liệu raw data (raw cumulative displacement before differencing) để tính toán increment giữa tháng thứ 36 và tháng thứ 42, thì bạn đã khái quát hóa thành một công thức để chúng ta không cần phải làm biến đổi phức tạp, phải không?
>
> Ví dụ nha, chuỗi cumulative displacement có các giá trị 0, -1, -3, -2, -3, -4, -3.5, -5, -6 và bị missing 5 lần đo, lần đo tiếp theo là -10, thì chúng ta biết được từ lần cuối là -6 tới -10 là giảm 4 đơn vị (chênh lệch là -4). Vậy là ta không biết 5 lần kia như thế nào, nhưng ta biết được tổng là -4, phải vậy không?

### Giải thích

Đúng về mặt toán học, nhưng đây không chỉ là một phép đơn giản hóa gần đúng. Tổng các gia số trong một khoảng bằng chính xác chênh lệch giữa hai giá trị cumulative displacement ở hai đầu khoảng, miễn là cả hai được xác định từ cùng một chuỗi đã căn chỉnh theo thời gian.

Gọi $D_t$ là cumulative displacement tại thời điểm $t$. Gia số trong một tháng được xác định bằng

$$
y_t=D_t-D_{t-1}.
$$

Tổng các gia số trong $H$ tháng là

$$
\sum_{h=1}^{H}y_{t+h}
=
\sum_{h=1}^{H}\left(D_{t+h}-D_{t+h-1}\right)
=
D_{t+H}-D_t.
$$

Các giá trị cumulative displacement nằm giữa hai đầu khoảng tự triệt tiêu khi các gia số được cộng lại. Quan hệ này thường được gọi là một *telescoping sum*. Vì vậy, không cần khôi phục từng giá trị cumulative displacement ở giữa để xác định tổng biến dạng của cả khoảng.

Trong ví dụ trên, giá trị cuối cùng trước khoảng thiếu là $-6$, còn quan trắc tiếp theo là $-10$. Tổng biến dạng giữa hai quan trắc là

$$
Y_I=-10-(-6)=-4.
$$

Giá trị $-4$ cho biết tổng biến dạng trong toàn khoảng nhưng không cho biết biến dạng của từng tháng. Các gia số hằng tháng bên trong khoảng có thể khác nhau và thậm chí có thể mang dấu khác nhau, miễn là tổng của chúng bằng $-4$. GWL và cGNSS hằng tháng cung cấp thông tin để mô hình ước tính cách tổng biến dạng này được phân bố theo tháng. Quan trắc tích lũy $-4$ sau đó được dùng như một ràng buộc cho tổng biến dạng của khoảng và để hiệu chỉnh lại mô hình trước chu trình kế tiếp.

Trong thí nghiệm hồi cứu hiện tại, pipeline đã có chuỗi monthly increments hoàn chỉnh trước khi các giá trị bên trong mỗi khoảng được che khỏi mô hình. Vì vậy, quan trắc tích lũy được tạo bằng

$$
Y_I=\sum_{t\in I}y_t.
$$

Nếu các monthly increments được tính nhất quán từ cùng một cumulative displacement series, phép cộng này tương đương chính xác với

$$
Y_I=D_{\mathrm{end}}-D_{\mathrm{start}}.
$$

Trong một lịch quan trắc thực tế chỉ có số đo cumulative displacement ở hai đầu khoảng, tổng biến dạng có thể được tính trực tiếp từ hiệu giữa hai số đo. Do đó, pipeline không cần quay lại raw cumulative displacement để thực hiện lại toàn bộ bước xử lý, miễn là monthly increments và các quan trắc đầu cuối cùng dùng một hệ quy chiếu và một cách căn chỉnh thời gian.

Một điểm cần lưu ý là số quan trắc bị thiếu không nhất thiết bằng số gia số thời gian. Nếu năm thời điểm đo nằm giữa $-6$ và $-10$ bị thiếu, thì hai quan trắc đầu cuối cách nhau sáu khoảng thời gian. Khi đó, $H_I$ phải được xác định từ số khoảng tháng giữa hai quan trắc, không phải chỉ từ số thời điểm bị thiếu.
