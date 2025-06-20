let newsData = [];
let filteredData = [];
let intervalId = null;
const spinner = document.getElementById('spinner');

async function fetchNews() {
  spinner.style.display = 'inline-block';
  try {
    // API real de notícias
    const res = await fetch('/api/articles/?limit=30&ordering=-collected_date');
    if (!res.ok) throw new Error('Falha ao buscar notícias');
    const data = await res.json();
    
    // Mapeia os dados da API para o formato esperado
    newsData = data.results.map(item => ({
        id: item.id,
        title: item.title,
        time: new Date(item.collected_date).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit'}),
        content: item.summary || item.content.substring(0, 100) + '...',
        category: item.categories.length > 0 ? item.categories[0].slug : 'general',
        url: item.url,
    }));

  } catch (err) {
    console.error(err);
    // fallback de exemplo
    newsData = [
      { id: 1, title: 'Exemplo 1: Falha na API', time: '12:00', content: 'Conteúdo 1', category: 'market', url: '#' },
      { id: 2, title: 'Exemplo 2', time: '12:02', content: 'Conteúdo 2', category: 'tech', url: '#' },
      { id: 3, title: 'Exemplo 3', time: '12:05', content: 'Conteúdo 3', category: 'economy', url: '#' }
    ];
  } finally {
    spinner.style.display = 'none';
    applyFilters();
  }
}

function renderNews(data) {
  const container = document.getElementById('news-container');
  container.innerHTML = '';
  data.forEach(item => {
    const box = document.createElement('div'); 
    box.className = 'box';
    
    // Mapeia slug da categoria para classe CSS
    const categoryClass = item.category.replace('-', '');
    
    box.innerHTML = `
      <div class="news-title">${item.title}</div>
      <div class="news-meta">${item.time}</div>
      <div class="news-content">${item.content}</div>
      <span class="category ${categoryClass}">${item.category.toUpperCase()}</span>
    `;
    box.onclick = () => window.open(item.url, '_blank');
    container.appendChild(box);
  });
  updateTicker(data);
}

function updateTicker(data) {
  const ticker = document.getElementById('news-ticker');
  ticker.innerHTML = '';
  const p = document.createElement('p');
  p.textContent = data.map(n => n.title).join('  •  ');
  ticker.appendChild(p);
}

function filterCategory(cat) {
  document.getElementById('search').value = '';
  filteredData = newsData.filter(n => cat === 'all' || n.category === cat);
  renderNews(filteredData);
}

function applyFilters() {
  const term = document.getElementById('search').value.toLowerCase();
  filteredData = newsData.filter(n => n.title.toLowerCase().includes(term) || n.content.toLowerCase().includes(term));
  renderNews(filteredData);
}

function updateInterval() {
  clearInterval(intervalId);
  const rate = parseInt(document.getElementById('refresh-rate').value, 10);
  intervalId = setInterval(fetchNews, rate);
}

window.onload = () => {
  fetchNews();
  updateInterval();
}; 