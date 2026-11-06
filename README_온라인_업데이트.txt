v18 | 2026-11-06

[더보기 수정]
데스크톱은 한 줄에 5권이므로 첫 화면에 15권(3줄), 더 보기도 15권씩 추가합니다.
태블릿/모바일은 반응형으로 4/3/2열입니다.

[온라인 배포 및 새 책 등록]
1. GitHub 저장소를 생성해 ZIP의 yeonseung-site 폴더 안 파일 전체를 저장소 최상위에 업로드합니다.
   .github/workflows/register-book.yml 과 tools/propose_book.py 도 포함해야 합니다.
2. GitHub Settings > Actions > General > Workflow permissions 에서 Read and write permissions 허용.
   PR 권한 생성도 허용해야 합니다.
3. Cloudflare Pages에서 Connect to Git 으로 해당 GitHub 저장소에 연결합니다.
   프레임워크 None, Build command 비움, Output directory / (또는 .), production branch main.
   Git 연동으로 새 프로젝트를 만들면 향후 main 브랜치 수정 시 자동 배포됩니다.
4. 새 책은 GitHub 저장소 > Actions > 새 책 등록 제안 > Run workflow 에서 제목만 입력할 수 있습니다.
   정확한 한국어판을 찾지 못할 경우 저자/출판사/연도/상세 URL/표지 URL을 추가 입력해 재실행합니다.
5. Actions가 생성한 Pull request에서 변경된 책 데이터와 이미지 확인 > Merge.
   Merge 후 Cloudflare Pages가 자동 배포합니다.

주의: 제목만 입력하면 항상 완전 자동으로 정확한 판본이 선택되는 것은 아닙니다.
불완전한 서지의 경우 books.js는 바꾸지 않고 BOOK_UPDATE_REVIEW.md에 문제를 기록합니다.
등록 확인 전에는 홈페이지가 바뀌지 않습니다. GitHub·Cloudflare 연결은 사용자가 직접 수행해야 합니다.
직접 업로드(Direct Upload)로 이미 만든 Pages 사이트는 Git 통합 방식으로 변환할 수 없으므로 Git 연동 새 프로젝트 생성이 필요할 수 있습니다.

기존 윈도우용 ADD_OR_UPDATE_BOOK.bat 도 남아 있지만 PC 로컬 파일만 수정합니다.
