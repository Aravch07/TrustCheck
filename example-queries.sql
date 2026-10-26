USE trustcheck_local;
SHOW TABLES;
DESCRIBE reviews;
SELECT b.name,COUNT(r.id) total_reviews,ROUND(AVG(r.rating),2) average_rating
FROM businesses b LEFT JOIN reviews r ON r.business_id=b.id GROUP BY b.id ORDER BY total_reviews DESC;
SELECT u.name,b.name business,COUNT(*) repeat_reviews
FROM reviews r JOIN reviewers u ON u.id=r.reviewer_id JOIN businesses b ON b.id=r.business_id
GROUP BY u.id,b.id HAVING COUNT(*)>=3 ORDER BY repeat_reviews DESC;
SELECT business_id,DATE_FORMAT(posted,'%Y-%m-%d %H:00') review_hour,COUNT(*) total
FROM reviews GROUP BY business_id,review_hour HAVING COUNT(*)>=6 ORDER BY total DESC;
SELECT business_id,body,COUNT(*) duplicate_texts FROM reviews
GROUP BY business_id,body HAVING COUNT(*)>=3 ORDER BY duplicate_texts DESC;
SELECT * FROM audit ORDER BY id DESC LIMIT 30;
-- Transaction demonstration: this change is rolled back.
START TRANSACTION;
UPDATE reviews SET status='Reviewed' WHERE id=1;
SELECT id,status FROM reviews WHERE id=1;
ROLLBACK;
