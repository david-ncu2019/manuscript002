# [SUPERSEDED 2026-08-25 — xem note mới `20260825_discuss52_restructure_note.md`]

> Toàn bộ nội dung bên dưới đã bị thay thế. Giữ lại nguyên văn chỉ để làm lịch sử tham khảo — **không
> dùng để viết prose**. Hai lỗi đã được tác giả phát hiện và tôi xác nhận đúng:
> 1. Con số endpoint 1.4–1.54 mm / 2.47–2.74 mm được gán nhầm là "§4.3" — thực ra thuộc §4.2
>    (`subsec:results_reduced_frequency`, đo thưa định kỳ). §4.3 là kịch bản khác hẳn (dừng hẳn
>    MLCW, không refit, không phải "đo thưa").
> 2. Diễn đạt "sai lệch tích lũy gần gấp đôi" ngụ ý sai một quan hệ tỷ lệ — endpoint 12 tháng cộng
>    dồn qua 12 monthly estimates, endpoint 6 tháng chỉ qua 6, nên không thể so sánh "gấp đôi" khi độ
>    dài tích lũy khác nhau. `discuss003.tex` dòng 175 (note) đã tự cảnh báo đúng điều này.
>
> Khung "field visit / WRA infrastructure" bên dưới cũng bị thay bằng một câu implication khác, không
> cần tới khung kinh tế mới — xem note mới.

---

# Đề xuất: định hướng người đọc kinh tế/vận hành cho discuss003.tex §5.2

**Phạm vi:** chỉ câu mở đầu `sections/discuss003.tex` dòng 38 (`subsec:discussion_reduced_mlcw_information`).
Không đụng §5.1, §5.3, Conclusions, không figure mới. Chưa sửa file — chờ tác giả duyệt.

**Câu hỏi gốc của tác giả:** liệu chỉ dùng dữ liệu quan trắc rẻ hơn (GWL + cGNSS) có thể cung cấp
thông tin layerwise subsurface compaction hay không, và nếu muốn giảm tần suất MLCW để tiết kiệm
thì nên giảm tới mức nào — cho đối tượng đọc là Water Resources Agency (WRA) hoặc công ty vận hành
mạng lưới MLCW.

---

## 3 câu hỏi mở cần tác giả quyết định trước khi sửa file

1. **Câu mở đầu đề xuất bên dưới có chấp nhận được không?** Đây là nội dung framing mới (không phải
   số liệu mới) — theo quy tắc `style.md`, framing mới cần tác giả xác nhận trước khi đưa vào bản thảo.
2. **`ms2_outline_v3_3_1.md` (06/08/2026) đã có sẵn khung WRA/kinh tế rất rõ** (trích dẫn bên dưới) —
   đây là chủ ý bị lược bớt trong các vòng sửa Q1–Q12, hay bị trôi mất ngoài ý muốn? Cấu trúc gộp §4
   của outline đó KHÔNG được áp dụng (main.tex vẫn tách `results004.tex`/`discuss003.tex`), nên bản
   thân outline này chỉ mang tính tham khảo — nhưng nội dung định hướng của nó có thể vẫn còn giá trị.
3. **Việc dùng chữ "field visit" (thao tác hiện trường) cho MLCW có đúng ý tác giả không?**
   `dataset003.tex` không dùng cụm này trực tiếp — đây là diễn giải hợp lý từ "monthly... measured...
   using... borehole extensometer systems" (dòng 4/10), nhưng là cách diễn đạt mới, cần xác nhận.

---

## Bằng chứng đã kiểm chứng trực tiếp trong phiên này (không suy đoán)

**Số liệu §4.2 khớp với draft câu mở đầu, đọc lại trực tiếp từ `results004.tex`:**
- MAE hàng tháng phẳng, không đơn điệu theo lịch đo: 0.27–0.31 mm/tháng trên cả 6 kịch bản (dòng 136).
- Sai lệch tích lũy tại điểm kiểm tra (endpoint) KHÔNG phẳng: 1.4–1.54 mm (lịch 6 tháng) so với
  2.47–2.74 mm (lịch 12 tháng) — dòng 174, xấp xỉ gấp đôi khi khoảng cách kiểm tra tăng gấp đôi.
- **Đây là tín hiệu thật duy nhất trả lời "giảm tới mức nào"** — nhưng chỉ là MỘT cặp điểm (6 tháng,
  12 tháng), không phải một đường cong liên tục. Không nên trình bày như thể đã có "trade-off curve"
  đầy đủ — nghiên cứu chỉ kiểm tra đúng 2 tần suất.

**Câu hỏi treo tại `results004.tex` dòng 175 ("6 tháng đầu của lịch 12 tháng so với 6 tháng đầy đủ
của lịch 6 tháng") đã có dữ liệu trả lời một phần**, từ `diag_27_sec4_2_matched_cycle_comparison`
(đã tính, đã verify trong phiên trước, CHƯA đưa vào bản thảo) — sai lệch dấu tại điểm kiểm tra giữa
kỳ triệt tiêu một phần ở 2/3 trường hợp độ dài lịch sử ban đầu, và co lại ở trường hợp còn lại. Đây
là việc riêng (Phần 0, đã hoãn theo quyết định trước đó của tác giả) — chỉ nhắc lại ở đây vì nó liên
quan trực tiếp, không tự ý viết vào bản thảo.

**Khung kinh tế "rẻ hơn" KHÔNG có cơ sở trong `dataset003.tex` (đã khóa, đã grep xác nhận: 0 lần
xuất hiện "cost/expense/budget"):**
- MLCW: đo hàng tháng qua "specialized borehole extensometer systems" tới độ sâu ~300 m (dòng 4, 10).
- GWL: "Daily piezometric head measurements," mạng lưới **do Water Resources Agency of Taiwan vận
  hành** (dòng 14) — đây là anchor đúng cho khán giả WRA.
- cGNSS: "Daily three-dimensional position time series," trạm TKJS **thuộc IESAS/TGM** (dòng 18) —
  **KHÔNG thuộc WRA**. Không được gộp chung cGNSS vào "hạ tầng WRA."
- Điểm chung đúng giữa GWL và cGNSS không phải "cùng thuộc WRA" mà là: cả hai đều tự động, hàng
  ngày, độc lập với lịch đo MLCW — đây là sự bất đối xứng thật, đã có trong §2, an toàn để dùng.

---

## Câu mở đầu đề xuất (thay dòng 38, giữ nguyên toàn bộ phần còn lại của đoạn)

> "For an operator weighing fewer scheduled MLCW field measurements against monitoring cost, the
> monthly groundwater-level and surface-displacement records already collected daily and
> independently of the MLCW schedule continue to inform the same-month compaction estimate between
> MLCW checks; what changes is how long an error can accumulate before the next MLCW measurement
> provides an independent check on it."

Câu hiện tại (dòng 38, phần đầu): *"The effect of reducing MLCW information was not uniform across
the tested measurement scenarios."* — không nêu effect của cái gì, cho ai, để làm gì; người đọc phải
đọc hết cả đoạn mới hiểu được câu hỏi đang được trả lời. Câu đề xuất chỉ thêm ngữ cảnh người đọc ở
đầu — không đổi số liệu, không đổi kết luận, không thêm khẳng định mới ngoài khung dữ kiện đã có.

**Dòng 50 (kết đoạn) đã đúng phạm vi, không cần sửa:** "This distinction is a scientific implication
of the tested scenarios rather than a field schedule..." — đây chính là ranh giới Value-of-Information
đúng đắn (định lượng thông tin mất đi, không kê toa lịch đo cụ thể) và khớp với dòng 65 (§5.3)'s
guardrail. Giữ nguyên.

---

## Trích dẫn song song — outline cũ vs bản thảo hiện tại (câu hỏi mở #2)

`ms2_outline_v3_3_1.md` dòng 157, 161 (06/08/2026, KHÔNG phải outline đang dùng, cấu trúc gộp §4 của
nó chưa từng được áp dụng):
> "reducing MLCW check-in frequency from monthly to every 6 or 12 months is an operationally real
> trade-off, not just a mathematical robustness test." ... "present the data as a trade-off curve
> between field-visit cost and estimation uncertainty ... a tool for the Water Resources Agency (WRA)
> to decide how much they can safely reduce sampling frequency without blinding themselves to
> critical subsidence events."

`discuss003.tex` dòng 50 (bản thảo hiện tại, đang dùng):
> "This distinction is a scientific implication of the tested scenarios rather than a field
> schedule, and its practical interpretation must remain within the evidence boundary established
> at Tuku."

Hai câu này không mâu thuẫn về sự thật — cả hai đều đồng ý nghiên cứu không kê toa lịch đo cụ thể.
Khác nhau ở TRỌNG TÂM: outline cũ chủ động gọi tên WRA và khung "trade-off curve" ngay từ đầu; bản
thảo hiện tại đợi tới cuối đoạn mới nói tới ranh giới, không đặt tên đối tượng đọc ở đâu cả.

**Severity:** Thấp — không có mâu thuẫn factual, chỉ là cơ hội cải thiện signposting cho đúng đối
tượng đọc mà tác giả vừa nêu rõ. Không chặn deadline nếu bỏ qua.
