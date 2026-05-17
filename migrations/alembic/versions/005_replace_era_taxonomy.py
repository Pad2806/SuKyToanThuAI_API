from alembic import op

revision = "005_replace_era_taxonomy"
down_revision = "004_admin_event_studio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO public.eras
          (id, slug, name, year_range, start_year, end_year, summary,
           cover_image, fallback_image, featured_event_ids, order_index)
        VALUES
          (
            'era-tien-su-hong-bang', 'tien-su-hong-bang', 'Thời Tiền Sử - Hồng Bàng',
            'Khoảng 40.000 TCN - 258 TCN', -40000, -258,
            'Giai đoạn hình thành cư trú, nông nghiệp, luyện kim và ký ức cộng đồng đầu tiên trên đất Việt, đặt nền cho truyền thuyết Hồng Bàng và văn hóa Đông Sơn.',
            '/images/eras/tien-su-hong-bang.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 1
          ),
          (
            'era-cac-vua-hung', 'cac-vua-hung', 'Thời Đại Các Vua Hùng',
            '2879 TCN - 258 TCN', -2879, -258,
            'Thời đại Văn Lang trong ký ức dựng nước, gắn với các Vua Hùng, trung tâm Phong Châu, trống đồng và cộng đồng cư dân Lạc Việt.',
            '/images/eras/cac-vua-hung.png', '/images/generated/parchment.png',
            ARRAY['event-hung-vuong','event-son-tinh-thuy-tinh']::text[], 2
          ),
          (
            'era-au-lac', 'au-lac', 'Nước Âu Lạc',
            '257 TCN - 179 TCN', -257, -179,
            'Thời An Dương Vương xây dựng Âu Lạc, nổi bật với thành Cổ Loa, tổ chức phòng thủ và bước phát triển nhà nước sơ khai.',
            '/images/eras/au-lac.png', '/images/generated/parchment.png',
            ARRAY['event-co-loa']::text[], 3
          ),
          (
            'era-bac-thuoc', 'bac-thuoc', 'Thời Kỳ Bắc Thuộc',
            '179 TCN - 938', -179, 938,
            'Hơn một nghìn năm bị các triều đại phương Bắc đô hộ nhưng bản sắc Việt vẫn bền bỉ qua làng xã, văn hóa và các cuộc khởi nghĩa giành quyền tự chủ.',
            '/images/eras/bac-thuoc.png', '/images/generated/parchment.png',
            ARRAY['event-hai-ba-trung','event-ba-trieu','event-bach-dang']::text[], 4
          ),
          (
            'era-ngo', 'ngo', 'Nhà Ngô',
            '939 - 965', 939, 965,
            'Triều đại mở đầu nền độc lập tự chủ sau chiến thắng Bạch Đằng, đặt nền cho quá trình xây dựng chính quyền riêng của người Việt.',
            '/images/eras/ngo.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 5
          ),
          (
            'era-dinh', 'dinh', 'Nhà Đinh',
            '968 - 980', 968, 980,
            'Thời Đinh Bộ Lĩnh thống nhất đất nước sau loạn 12 sứ quân, đặt quốc hiệu Đại Cồ Việt và xây dựng kinh đô Hoa Lư.',
            '/images/eras/dinh.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 6
          ),
          (
            'era-tien-le', 'tien-le', 'Nhà Tiền Lê',
            '980 - 1009', 980, 1009,
            'Triều đại củng cố Đại Cồ Việt, chống Tống, bình Chiêm và tiếp tục xây nền hành chính quân chủ thời đầu độc lập.',
            '/images/eras/tien-le.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 7
          ),
          (
            'era-ly', 'ly', 'Nhà Lý',
            '1009 - 1225', 1009, 1225,
            'Thời dời đô ra Thăng Long, xây dựng quốc gia Đại Việt ổn định, phát triển Phật giáo, luật pháp, văn hóa và phòng thủ biên cương.',
            '/images/eras/ly.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 8
          ),
          (
            'era-tran', 'tran', 'Nhà Trần',
            '1225 - 1400', 1225, 1400,
            'Triều đại gắn với hào khí Đông A, ba lần kháng chiến chống Nguyên - Mông, cùng nhiều thành tựu quân sự, văn hóa và tổ chức nhà nước.',
            '/images/eras/tran.png', '/images/generated/parchment.png',
            ARRAY['event-bach-dang-1288']::text[], 9
          ),
          (
            'era-ho-minh-thuoc', 'ho-minh-thuoc', 'Nhà Hồ & Minh Thuộc',
            '1400 - 1427', 1400, 1427,
            'Giai đoạn biến động từ cải cách nhà Hồ đến ách đô hộ nhà Minh, dẫn tới phong trào Lam Sơn khôi phục nền độc lập.',
            '/images/eras/ho-minh-thuoc.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 10
          ),
          (
            'era-hau-le', 'hau-le', 'Nhà Hậu Lê',
            '1428 - 1789', 1428, 1789,
            'Thời kỳ phục hưng và mở rộng của Đại Việt sau khởi nghĩa Lam Sơn, nổi bật với luật Hồng Đức, giáo dục Nho học và biến động chính trị kéo dài.',
            '/images/eras/hau-le.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 11
          ),
          (
            'era-mac', 'mac', 'Nhà Mạc',
            '1527 - 1677', 1527, 1677,
            'Triều Mạc xuất hiện trong bối cảnh khủng hoảng cuối Lê sơ, tạo nên cục diện tranh chấp quyền lực và chia cắt kéo dài.',
            '/images/eras/mac.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 12
          ),
          (
            'era-le-trung-hung', 'le-trung-hung', 'Nhà Lê Trung Hưng',
            '1627 - 1777', 1627, 1777,
            'Giai đoạn quyền lực vua Lê - chúa Trịnh ở Đàng Ngoài song song với cục diện phân tranh, làm thay đổi cấu trúc chính trị và xã hội Đại Việt.',
            '/images/eras/le-trung-hung.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 13
          ),
          (
            'era-tay-son', 'tay-son', 'Triều Đại Tây Sơn',
            '1778 - 1802', 1778, 1802,
            'Phong trào Tây Sơn bùng nổ, lật đổ các thế lực cũ, thống nhất đất nước trong thời gian ngắn và ghi dấu bằng nhiều chiến thắng lớn.',
            '/images/eras/tay-son.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 14
          ),
          (
            'era-nguyen', 'nguyen', 'Nhà Nguyễn',
            '1802 - 1945', 1802, 1945,
            'Triều đại quân chủ cuối cùng của Việt Nam, thống nhất lãnh thổ, xây dựng kinh đô Huế và chứng kiến quá trình mất dần chủ quyền trước thực dân Pháp.',
            '/images/eras/nguyen.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 15
          ),
          (
            'era-phap-thuoc', 'phap-thuoc', 'Thời Kỳ Pháp Thuộc',
            '1884 - 1945', 1884, 1945,
            'Thời kỳ Việt Nam nằm dưới ách thống trị thực dân Pháp, xã hội biến đổi sâu sắc và các phong trào yêu nước, cải cách, cách mạng liên tục phát triển.',
            '/images/eras/phap-thuoc.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 16
          ),
          (
            'era-khang-chien-chong-phap', 'khang-chien-chong-phap', 'Kháng chiến Chống Pháp',
            '1945 - 1954', 1945, 1954,
            'Cuộc kháng chiến bảo vệ nền độc lập non trẻ, kết thúc bằng chiến thắng Điện Biên Phủ và Hiệp định Genève.',
            '/images/eras/khang-chien-chong-phap.png', '/images/generated/parchment.png',
            ARRAY['event-dien-bien-phu-1954']::text[], 17
          ),
          (
            'era-khang-chien-chong-my', 'khang-chien-chong-my', 'Kháng chiến Chống Mỹ',
            '1954 - 1975', 1954, 1975,
            'Giai đoạn đất nước tạm thời chia cắt và cuộc kháng chiến kéo dài nhằm thống nhất đất nước, kết thúc vào năm 1975.',
            '/images/eras/khang-chien-chong-my.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 18
          ),
          (
            'era-viet-nam-hien-dai', 'viet-nam-hien-dai', 'Thống nhất đất nước - Việt Nam Hiện Đại',
            '1975 - nay', 1975, NULL,
            'Từ sau thống nhất, Việt Nam bước vào tái thiết, đổi mới và hội nhập, tiếp tục chuyển mình trong đời sống kinh tế, văn hóa, xã hội và vị thế quốc tế.',
            '/images/eras/viet-nam-hien-dai.png', '/images/generated/parchment.png',
            ARRAY[]::text[], 19
          )
        ON CONFLICT (id) DO UPDATE SET
          slug=EXCLUDED.slug,
          name=EXCLUDED.name,
          year_range=EXCLUDED.year_range,
          start_year=EXCLUDED.start_year,
          end_year=EXCLUDED.end_year,
          summary=EXCLUDED.summary,
          cover_image=EXCLUDED.cover_image,
          fallback_image=EXCLUDED.fallback_image,
          featured_event_ids=EXCLUDED.featured_event_ids,
          order_index=EXCLUDED.order_index,
          updated_at=now()
        """
    )
    _remap_event_slugs()
    _remap_legacy_eras()
    op.execute(
        """
        DELETE FROM public.eras
        WHERE id IN (
          'era-van-lang-au-lac',
          'era-dinh-le',
          'era-ly-tran',
          'era-ho-le-so',
          'era-nam-bac-trieu',
          'era-hien-dai'
        )
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1
            FROM public.events e
            LEFT JOIN public.eras er ON er.id = e.era_id
            WHERE er.id IS NULL
          ) THEN
            RAISE EXCEPTION 'Era taxonomy replacement left events with missing eras';
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Forward-only content taxonomy replacement. Event rows are preserved.
    pass


def _remap_event_slugs() -> None:
    for slug, era_id, era_slug in (
        ("hung-vuong-dung-nuoc", "era-cac-vua-hung", "cac-vua-hung"),
        ("truyen-thuyet-son-tinh-thuy-tinh", "era-cac-vua-hung", "cac-vua-hung"),
        ("thanh-co-co-loa", "era-au-lac", "au-lac"),
        ("chien-thang-bach-dang-1288", "era-tran", "tran"),
        ("chien-thang-dien-bien-phu-1954", "era-khang-chien-chong-phap", "khang-chien-chong-phap"),
    ):
        op.execute(
            f"""
            UPDATE public.events
            SET era_id = '{era_id}', era_slug = '{era_slug}', updated_at = now()
            WHERE slug = '{slug}' OR id = '{slug}'
            """
        )


def _remap_legacy_eras() -> None:
    op.execute(
        """
        UPDATE public.events
        SET
          era_id = CASE
            WHEN era_id = 'era-van-lang-au-lac' AND year >= -257 THEN 'era-au-lac'
            WHEN era_id = 'era-van-lang-au-lac' AND year < -2879 THEN 'era-tien-su-hong-bang'
            WHEN era_id = 'era-van-lang-au-lac' THEN 'era-cac-vua-hung'
            WHEN era_id = 'era-dinh-le' AND year < 980 THEN 'era-dinh'
            WHEN era_id = 'era-dinh-le' THEN 'era-tien-le'
            WHEN era_id = 'era-ly-tran' AND year < 1225 THEN 'era-ly'
            WHEN era_id = 'era-ly-tran' THEN 'era-tran'
            WHEN era_id = 'era-ho-le-so' AND year < 1428 THEN 'era-ho-minh-thuoc'
            WHEN era_id = 'era-ho-le-so' THEN 'era-hau-le'
            WHEN era_id = 'era-nam-bac-trieu' AND year >= 1778 THEN 'era-tay-son'
            WHEN era_id = 'era-nam-bac-trieu' AND year >= 1627 THEN 'era-le-trung-hung'
            WHEN era_id = 'era-nam-bac-trieu' AND year >= 1527 THEN 'era-mac'
            WHEN era_id = 'era-nam-bac-trieu' THEN 'era-hau-le'
            WHEN era_id = 'era-hien-dai' AND year <= 1954 THEN 'era-khang-chien-chong-phap'
            WHEN era_id = 'era-hien-dai' AND year <= 1975 THEN 'era-khang-chien-chong-my'
            WHEN era_id = 'era-hien-dai' THEN 'era-viet-nam-hien-dai'
            ELSE era_id
          END,
          era_slug = CASE
            WHEN era_id = 'era-van-lang-au-lac' AND year >= -257 THEN 'au-lac'
            WHEN era_id = 'era-van-lang-au-lac' AND year < -2879 THEN 'tien-su-hong-bang'
            WHEN era_id = 'era-van-lang-au-lac' THEN 'cac-vua-hung'
            WHEN era_id = 'era-dinh-le' AND year < 980 THEN 'dinh'
            WHEN era_id = 'era-dinh-le' THEN 'tien-le'
            WHEN era_id = 'era-ly-tran' AND year < 1225 THEN 'ly'
            WHEN era_id = 'era-ly-tran' THEN 'tran'
            WHEN era_id = 'era-ho-le-so' AND year < 1428 THEN 'ho-minh-thuoc'
            WHEN era_id = 'era-ho-le-so' THEN 'hau-le'
            WHEN era_id = 'era-nam-bac-trieu' AND year >= 1778 THEN 'tay-son'
            WHEN era_id = 'era-nam-bac-trieu' AND year >= 1627 THEN 'le-trung-hung'
            WHEN era_id = 'era-nam-bac-trieu' AND year >= 1527 THEN 'mac'
            WHEN era_id = 'era-nam-bac-trieu' THEN 'hau-le'
            WHEN era_id = 'era-hien-dai' AND year <= 1954 THEN 'khang-chien-chong-phap'
            WHEN era_id = 'era-hien-dai' AND year <= 1975 THEN 'khang-chien-chong-my'
            WHEN era_id = 'era-hien-dai' THEN 'viet-nam-hien-dai'
            ELSE era_slug
          END,
          updated_at = now()
        WHERE era_id IN (
          'era-van-lang-au-lac',
          'era-dinh-le',
          'era-ly-tran',
          'era-ho-le-so',
          'era-nam-bac-trieu',
          'era-hien-dai'
        )
        """
    )
