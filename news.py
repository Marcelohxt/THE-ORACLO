import scrapy

class NewsHeadlineSpider(scrapy.Spider):
    name = "news_headline"
    # Lista de sites para coleta
    start_urls = [
        # Brasil
        'https://g1.globo.com',
        'https://noticias.uol.com.br',
        'https://noticias.r7.com',
        'https://www.cnnbrasil.com.br',
        'https://www.folha.uol.com.br',
        'https://www.estadao.com.br',
        'https://oglobo.globo.com',
        'https://www.terra.com.br/noticias/',
        'https://www.poder360.com.br',
        'https://agenciabrasil.ebc.com.br',
        # EUA
        'https://www.cnn.com',
        'https://www.foxnews.com',
        'https://www.nytimes.com',
        'https://www.washingtonpost.com',
        'https://www.nbcnews.com',
        'https://abcnews.go.com',
        'https://www.bloomberg.com',
        'https://www.reuters.com',
        'https://apnews.com',
        'https://www.cnbc.com',
        # Reino Unido
        'https://www.bbc.com/news',
        'https://www.theguardian.com',
        'https://www.telegraph.co.uk',
        # França
        'https://www.lemonde.fr',
        'https://www.france24.com',
        # Alemanha
        'https://www.dw.com',
        'https://www.spiegel.de',
        # Espanha
        'https://elpais.com',
        'https://www.elmundo.es',
        # Japão
        'https://www3.nhk.or.jp/nhkworld/en/',
        # China
        'https://www.cgtn.com',
        # Índia
        'https://timesofindia.indiatimes.com',
        'https://www.thehindu.com',
        # América Latina
        'https://www.clarin.com',
        'https://www.eluniversal.com.mx',
    ]

    def parse(self, response):
        # Tenta extrair a manchete principal
        headline = response.css('h1::text').get()
        if not headline:
            headline = response.css('title::text').get()

        # Extrai o primeiro parágrafo da matéria
        first_para = response.css('p::text').get()

        yield {
            'source': response.url,
            'headline': headline.strip() if headline else None,
            'first_paragraph': first_para.strip() if first_para else None,
            'article_link': response.url,
        }

        # Opcional: seguir links para mais páginas dentro do mesmo domínio
        for a in response.css('a::attr(href)').getall():
            if a and a.startswith('/'):
                a = response.urljoin(a)
            if a and response.url.split('/')[2] in a:
                yield scrapy.Request(a, callback=self.parse)
