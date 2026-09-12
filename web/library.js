(() => {
  const search=document.querySelector('#search'),level=document.querySelector('#level');
  const cards=[...document.querySelectorAll('.book-card')];
  function filter(){
    const words=search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    let count=0;
    for(const card of cards){card.hidden=!words.every(word=>card.dataset.search.includes(word))||(level.value&&card.dataset.level!==level.value);if(!card.hidden)count++;}
    document.querySelector('#results').textContent=`${count} ${count===1?'story':'stories'} ready to explore`;
    document.querySelector('#empty').hidden=count!==0;
  }
  search.addEventListener('input',filter);level.addEventListener('change',filter);filter();
})();
