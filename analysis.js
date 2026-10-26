// Each review receives five rule scores. Total possible score = 100.
// A flag suggests investigation; it does not prove a review is fake.

function average(reviews) {
  if (reviews.length === 0) return 0;
  let total = 0;
  for (const review of reviews) total += review.rating;
  return total / reviews.length;
}

// Similarity = shared words / all unique words (Jaccard similarity).
function similarity(firstText, secondText) {
  function words(text) {
    return text.toLowerCase().replace(/[^a-z ]/g, "").split(/\s+/)
      .filter(word => word.length > 2);
  }
  const first = new Set(words(firstText));
  const second = new Set(words(secondText));
  const allWords = new Set([...first, ...second]);
  let sharedWords = 0;
  for (const word of first) {
    if (second.has(word)) sharedWords++;
  }
  return sharedWords / Math.max(allWords.size, 1);
}

export function analyze(reviews) {
  return reviews.map(review => {
    const others = reviews.filter(other =>
      other.business_id === review.business_id && other.id !== review.id);
    const time = Date.parse(review.posted);
    const hour = 60 * 60 * 1000;
    const day = 24 * hour;

    const nearby = others.filter(other =>
      Math.abs(Date.parse(other.posted) - time) <= hour);
    const similar = others.filter(other =>
      similarity(review.body, other.body) >= 0.7);
    const repeated = others.filter(other =>
      other.reviewer_id === review.reviewer_id);
    const earlier = others.filter(other => Date.parse(other.posted) < time - day);
    const daily = others.filter(other =>
      Math.abs(Date.parse(other.posted) - time) <= day);

    const surge = earlier.length >= 5 && daily.length >= 5 &&
      average(daily) - average(earlier) > 1;
    const mismatch = earlier.length >= 5 &&
      Math.abs(review.rating - average(earlier)) >= 2;

    const signals = [
      { name: "Review burst", points: nearby.length >= 5 ? 25 : 0,
        detail: nearby.length + " other reviews within one hour" },
      { name: "Similar wording", points: similar.length >= 2 ? 25 : 0,
        detail: similar.length + " reviews with at least 70% word overlap" },
      { name: "Rating surge", points: surge ? 20 : 0,
        detail: "Daily mean rises over 1 star versus earlier reviews; at least 5 reviews per group" },
      { name: "Repeat reviewer", points: repeated.length >= 2 ? 20 : 0,
        detail: (repeated.length + 1) + " reviews of this business by this account" },
      { name: "Rating mismatch", points: mismatch ? 10 : 0,
        detail: "Rating differs from the earlier mean by at least 2 stars; at least 5 earlier reviews" }
    ];

    let score = 0;
    for (const signal of signals) score += signal.points;
    return { ...review, signals, score };
  });
}
