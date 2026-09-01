# Phân biệt displacement và deformation trong manuscript

**Thời điểm:** 2026/09/01 23:22:57 (Asia/Taipei)

## Cách hiểu ngắn gọn

`Displacement` và `deformation` không phải là hai cách gọi của cùng một đại lượng. **Displacement** cho biết một điểm đã di chuyển bao xa và theo hướng nào so với vị trí tham chiếu. **Deformation** cho biết khoảng cách tương đối giữa nhiều điểm trong vật liệu đã thay đổi ra sao. Vì vậy, displacement mô tả chuyển động của một điểm, còn deformation mô tả sự thay đổi hình dạng hoặc độ dày của vật thể nằm giữa các điểm đó.

| Khái niệm | Câu hỏi mà đại lượng trả lời | Ví dụ trong nghiên cứu | Đơn vị thường dùng |
|---|---|---|---|
| Displacement | Một điểm đã di chuyển bao xa và theo hướng nào? | Chuyển vị thẳng đứng của mốc cGNSS tại mặt đất | mm |
| Deformation | Vật liệu giữa hai hoặc nhiều điểm đã co lại, giãn ra, hay đổi hình dạng bao nhiêu? | Độ co lại hoặc giãn nở trong một section của MLCW | mm |
| Strain | Mức thay đổi độ dày lớn đến đâu so với độ dày ban đầu? | Deformation của một section chia cho bề dày section | Không có đơn vị, hoặc microstrain |

## Ví dụ với hai mốc quan trắc

Giả sử hai mốc A và B nằm cách nhau 50 m theo chiều sâu.

```text
Ban đầu

A  --------------------  mốc trên
|                       |
|       50 m đất        |
|                       |
B  --------------------  mốc dưới
```

### Trường hợp 1: cả hai mốc cùng dịch chuyển như nhau

Nếu A và B đều đi xuống 10 mm, mỗi mốc có displacement 10 mm. Tuy nhiên, khoảng cách giữa A và B vẫn là 50 m. Toàn bộ khối đất chỉ tịnh tiến xuống dưới mà không thay đổi độ dày. Trường hợp này có **displacement nhưng không có deformation trong khoảng A--B**.

```text
A: đi xuống 10 mm
B: đi xuống 10 mm

Chuyển động tương đối = 10 - 10 = 0 mm
Thay đổi độ dày lớp đất = 0 mm
```

### Trường hợp 2: hai mốc dịch chuyển khác nhau

Nếu A đi xuống 10 mm nhưng B chỉ đi xuống 4 mm, A tiến gần B thêm 6 mm. Khoảng đất A--B vì vậy mỏng đi 6 mm. Hai mốc đều có displacement, còn chênh lệch 6 mm giữa chúng biểu thị deformation của khoảng đất. Trong trường hợp này, deformation là **compaction**.

```text
A: đi xuống 10 mm
B: đi xuống  4 mm

Chuyển động tương đối = 10 - 4 = 6 mm
Độ co lại của lớp đất = 6 mm
```

Nếu mốc trên và mốc dưới đi xa nhau, khoảng đất dày lên. Deformation khi đó là **expansion**.

## Quan hệ toán học

Gọi \(u_{\mathrm{upper}}\) và \(u_{\mathrm{lower}}\) là displacement của hai mốc giới hạn một khoảng độ sâu. Chuyển động tương đối của hai mốc là

\[
\Delta u_{\mathrm{relative}}
=u_{\mathrm{upper}}-u_{\mathrm{lower}}.
\]

Độ lớn của \(\Delta u_{\mathrm{relative}}\) cho biết độ dày của khoảng đất đã thay đổi bao nhiêu. Dấu dương hay âm biểu thị compaction hay expansion tùy theo quy ước chiều dương của bộ dữ liệu. Nếu cần so sánh các khoảng có bề dày khác nhau, deformation có thể được chuẩn hóa thành vertical strain:

\[
\varepsilon_z
=\frac{\Delta u_{\mathrm{relative}}}{H},
\]

trong đó \(H\) là bề dày ban đầu của khoảng đất. Manuscript hiện báo cáo deformation increment bằng mm hoặc mm/month, không phải strain, nên không cần đưa \(\varepsilon_z\) vào bài nếu không thực sự sử dụng đại lượng này.

## Hai thiết bị trong manuscript đo gì?

**cGNSS đo displacement tại một điểm trên mặt đất.** Đại lượng này cho biết mốc cGNSS đã di chuyển thẳng đứng bao nhiêu. Nó phản ánh chuyển động tổng hợp của vật liệu bên dưới mốc, kể cả deformation có thể xảy ra bên dưới độ sâu mà MLCW quan trắc. Vì chỉ quan sát một điểm ở mặt đất, cGNSS không tự nó cho biết section nào đã đóng góp bao nhiêu vào chuyển động đó.

**MLCW đo displacement tương đối tại nhiều độ sâu.** Chênh lệch displacement giữa hai vòng neo liên tiếp cho biết deformation của khoảng đất nằm giữa chúng. MLCW vì vậy có thể phân chia tổng chuyển động theo phương đứng thành deformation của từng khoảng độ sâu. Đây là thông tin mà một mốc cGNSS tại mặt đất không thể cung cấp trực tiếp.

Quan hệ giữa hai nguồn quan trắc có thể tóm tắt như sau:

```text
Deformation trong section S1
             +
Deformation trong section S2
             +
             ...
             +
Deformation trong vật liệu sâu hơn
             |
             v
Vertical displacement quan sát tại mặt đất
```

Sơ đồ này chỉ mô tả mối quan hệ vật lý tổng quát. Chuyển vị cGNSS không nhất thiết bằng đúng tổng deformation của sáu section MLCW, vì cGNSS còn có thể ghi nhận chuyển động phát sinh bên dưới độ sâu quan trắc của MLCW và các thành phần chuyển động khác.

## Cách dùng từ nhất quán trong manuscript

1. Đối với đại lượng cGNSS, nên viết **`vertical displacement measured by cGNSS`** hoặc **`vertical displacement at the ground surface`**. Nếu muốn nhấn mạnh đây là chuyển động tổng hợp, có thể viết **`total vertical displacement measured by cGNSS`**.
2. Đối với đại lượng MLCW trong từng section, nên viết **`deformation within individual depth sections`**, **`deformation by depth interval`**, hoặc cụ thể hơn là **`compaction or expansion within a depth interval`**.
3. Không nên gọi số liệu thô của cGNSS là `surface deformation` nếu mục đích là mô tả chính xác phép đo. cGNSS trực tiếp ghi displacement của mốc quan trắc. Từ deformation phù hợp khi diễn giải sự thay đổi bên trong vật liệu hoặc sự thay đổi của một trường displacement trong không gian.
4. `Land subsidence` là chuyển động đi xuống của mặt đất được xem như một hiện tượng hoặc hiểm họa. Nó gần với vertical surface displacement, nhưng không thay thế cho khái niệm deformation trong từng lớp đất.

## Hệ quả đối với câu kết của manuscript

Câu take-home nên giữ rõ vai trò của từng thành phần: hydraulic head mô tả điều kiện thủy lực, cGNSS cung cấp total vertical displacement tại mặt đất, Bayesian ridge regression liên hệ hai nguồn thông tin này với deformation theo độ sâu, và MLCW cung cấp quan trắc trực tiếp để đánh giá các ước tính đó. Một cách viết chính xác là:

> Bayesian ridge regression can combine monthly hydraulic head observations with cGNSS measurements of total vertical displacement to estimate deformation between MLCW observations, while each new MLCW measurement shows how accurately those estimates represent deformation accumulated within individual depth sections.

Câu này không nói cGNSS trực tiếp đo deformation của từng section. Nó cũng không nói mô hình thay thế MLCW. Thay vào đó, câu văn phân biệt rõ ba vai trò: cGNSS đo chuyển động tổng hợp tại mặt đất, mô hình ước tính deformation theo độ sâu, và MLCW cung cấp phép đo trực tiếp theo độ sâu để đánh giá kết quả.
