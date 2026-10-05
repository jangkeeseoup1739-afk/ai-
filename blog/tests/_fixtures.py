"""테스트용 가짜 네이버 글 페이지. 스마트에디터 ONE 구조를 흉내낸다."""
from __future__ import annotations


def post_html(title: str, paragraphs: list[str], images: int = 0, videos: int = 0,
              headings: list[str] | None = None, tags: list[str] | None = None,
              published: str = "2026. 9. 1. 10:30", links: list[str] | None = None,
              maps: int = 0) -> str:
    body = []
    for h in headings or []:
        body.append(f'<div class="se-component se-section-sectionTitle">'
                    f'<p class="se-text-paragraph"><span>{h}</span></p></div>')
    for p in paragraphs:
        body.append('<div class="se-module se-module-text">'
                    f'<p class="se-text-paragraph"><span>{p}</span></p></div>')
    for i in range(images):
        body.append(f'<div class="se-component se-module-image">'
                    f'<img class="se-image-resource" src="img{i}.jpg"></div>')
    for i in range(videos):
        body.append('<div class="se-component se-module-video">'
                    '<iframe src="https://serviceapi.nmv.naver.com/v1"></iframe></div>')
    for i in range(maps):
        body.append('<div class="se-component se-module-map">지도</div>')
    for href in links or []:
        body.append(f'<a href="{href}">링크</a>')

    tag_html = ""
    if tags:
        tag_html = ('<div class="post_tag">'
                    + "".join(f'<a href="#">#{t}</a>' for t in tags)
                    + "</div>")
    return f"""<!doctype html><html><head>
<meta property="og:title" content="{title} : 네이버 블로그">
</head><body>
<div class="se-module se-module-text se-title-text"><p><span>{title}</span></p></div>
<span class="se_publishDate pcol2">{published}</span>
<div class="se-main-container">{''.join(body)}</div>
<div class="se-module-sticker"></div>
{tag_html}
</body></html>"""


def long_post(keyword: str = "상추", n: int = 40) -> str:
    """점수가 잘 나와야 하는 글. 키워드 밀도도 권장 범위에 들어가게 만든다."""
    paras = [f"{keyword} 처음 심을 때 흙만 바꿨더니 3주 만에 수확했습니다. 결론부터 쓰면 배수가 전부입니다."]
    for i in range(n):
        if i % 3 == 0:
            paras.append(f"{keyword} 를 심은 {i + 1}주차에는 물을 이틀에 한 번 "
                         f"{200 + i}ml 줬습니다. 직접 재보니 흙 깊이는 15센티가 적당했습니다.")
        else:
            paras.append(f"{i + 1}주차에는 잎이 {i + 2}장 늘었고, 벌레는 손으로 잡아 "
                         "약을 치지 않았습니다. 베란다 온도는 22도를 유지했습니다.")
    return post_html(
        f"{keyword} 키우는 방법 총정리 (초보 기준)",
        paras,
        images=7, videos=1,
        headings=[f"{keyword} 흙 고르기", f"{keyword} 물 주기", f"{keyword} 수확 시기"],
        tags=[keyword, "텃밭", "베란다텃밭", "상추키우기", "주말농장", "초보텃밭"],
        links=["https://blog.naver.com/myid/111", "https://example.com/shop"],
    )


def thin_post(title: str = "오늘 다녀왔어요") -> str:
    """점수가 낮아야 하는 글."""
    return post_html(title, ["안녕하세요. 오늘은 그냥 다녀온 이야기입니다.",
                             "날씨가 좋았어요. 다음에 또 가야겠습니다."],
                     images=1)
