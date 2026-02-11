- File Handling (PDF/TXT/CSV)
  + Combine file and text input
  + PDF, word , txt 
  + Excel, csv ( đọc nội dung file trước rồi)
  + Limit: size of file , length of file, type
- Security & Safety test ( in test plan ) ( done )
- Error handling + retry ( phải có ochestrator process xử lý retry chứ nhỉ ) ( retry queue vẫn dùng service kafka, Dead Letter Queue dùng lại mongodb service) ( done )
- Unit test +  Unit test report ( done )
- Rà soát 1 lượt lỗ hổng bảo mật , ratelimit ( done )
- Check upload rag doc ( có upload thẳng lên không , upload xong phải sửa ở frontend ) ( done)
- Deploy + retest ( done )
- Check 1 lượt .env ( done )
- Tính năng upload file có lưu lại file không ( done )
- Define functions for each module ( especial dataflow ( handle and save analystic data ) ) ( done )
- Achitecture chart ( done ) ( chưa cho Ilank biêt )
- Scale Plan ( done )
- Error handling plan (retry) ( done )
- Testing Plan ( just create a plan ) ( done )
  + Manual test by simulating browser 
  + Stress test 
- Quay video test hỏi mấy câu về code trông trả lời cho ngầu + trình bày cả phần responsive ( do before deploy ) ( done)
- Let PM know about sercurity ( security.md )
- Let PM know about streaming ( stream_response.md )