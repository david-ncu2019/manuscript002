# Manuscript Outline (v2)

- **1 Introduction**
[NOTE: phần này chỉ cần viết đại khái, bởi vì phần này rất quan trọng, phải có nhiều trích dẫn để bổ sung literature review]

- **2 Study Area and Datasets** [NOTE: đã ổn, đừng chỉnh sửa]
  - 2.1 Study Area Background
  - 2.2 Datasets
    - 2.2.1 Multilayer aquifer-system compaction
    - 2.2.2 Groundwater level observations
    - 2.2.3 Vertical surface displacement
    - 2.2.4 Borehole lithological profile
- **3 Methodology** [NOTE: phần 3.1 đã ổn, đừng chỉnh sửa]
  - 3.1 Preparation of model inputs
    - 3.1.1 Deformation time series model
    - 3.1.2 Isometric logratio transformation of sediment composition
    - 3.1.3 Assembly of monthly model inputs
    [NOTE: tất cả các mục từ 3.1.3 trở lên là không được đụng tới vì đã sửa xong]

  - 3.2 Bayesian ridge regression
  [NOTE: mục tiêu chính của đoạn này không phải là trình bày lý do tại sao tui chọn mô hình này, cái đó sẽ được trình bày chủ yếu ở section Introduction, sau đó lý do này sẽ được nhắc lại đại khái ở đầu mục 3.2. phần nội dung chính phải là giải thích thuật toán một cách rõ ràng, dễ hiểu, bám sát những gì mà bài báo "D:\001_LITERATURE_v2\ZOTERO_storage\Pedregosa et al. - Scikit-learn Machine Learning in Python.pdf" và trang https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.BayesianRidge.html#sklearn.linear_model.BayesianRidge đã trình bày]
  
  [NOTE: chúng ta phải trình bày 2 phần sau 3.2, (1) là làm sao mô hình đưa ra được khoảng dự đoán uncertainty cho kết quả, chúng chỉ cần viết quy tắc chung chứ không cần phải viết các tính uncertainty cho mỗi thí nghiệm được thiết kế sau đó, () là thiết kế thí nghiệm. trong phần (2) thiết kế thí nghiệm sẽ tiếp tục chia làm 2 phần. phần (2a) là trường hợp đo đạc tới trễ 6 tháng, nhưng khi đã được gửi thì sẽ đủ đo đạc của mỗi tháng trong 6 tháng qua. phần (2b) là giả định rằng nhà cung cấp chỉ quan trắc N tháng 1 lần, N ở đây = 6 và = 12. chúng ta chưa phát triển scripts cho trường hợp (2b) nhưng chúng ta sẽ sớm giải quyết nó.].
  ~~3.3 Model evaluation and uncertainty
    ~~3.3.1 Evaluation with delayed MLCW data availability~~
    ~~3.3.2 Prediction intervals~~
    ~~3.3.3 Sensitivity to less frequent MLCW measurements~~
- **4 Results and discussion**
  [NOTE: phần này chỉ cần chứng minh cho độc giả thấy được phương pháp của chúng ta vẫn đưa ra các dựa đoán gần sát với MLCW thực tế, dù chỉ sử dụng các đại lượng đơn giản như. chúng ta phải thuyết phục độc giả rằng phương pháp của chúng ta có thể giúp dự đoán layerwise compaction bằng các dữ liệu rẻ tiền hơn và có mạng lưới dày đặc hơn. . Về phần thảo luận, hai cái mục `Sensitivity to MLCW measurements collected every N months` nên đước gộp lại nói ngắn gọn thay vì phân ra từng mục nhỏ. và tui nghĩ bạn hãy giúp tui suy nghĩ thêm chúng ta phải trưng ra kết quả gì và thảo luận gì, chứ chỉ có 2 mục thì không đủ]
  - ~~4.1 Monthly compaction nowcasting during delayed MLCW data availability~~
  - ~~4.2 Sensitivity to MLCW measurements collected every six months~~
  - ~~4.3 Sensitivity to MLCW measurements collected every twelve months~~
- **5 Conclusions**
  [NOTE: nhắc lại mục tiêu của bài này, dữ liệu và phương pháp được sử dụng, kết quả có khả thi không? có đưa ra kết luận gì?]
- **A Supplementary methodological details**
  [NOTE: phần này nên để làm nơi tạm chứa những ý tưởng, và sẽ chính sửa lại sau khi các phần trên đã được thiết kế ổn thõa]
  - A.1 Final predictor inventory
  - A.2 Model fitting and update settings
  - A.3 Prediction interval calibration
  - A.4 Reduced-frequency MLCW measurement settings
