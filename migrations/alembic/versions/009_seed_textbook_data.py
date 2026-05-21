"""Seed textbook parts and lessons for grades 8-12 (Lịch sử SGK)."""

from alembic import op

revision = "009_seed_textbook_data"
down_revision = "008_tactical_climax_slots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make event_id nullable so lessons can exist before events are assigned
    op.execute(
        "ALTER TABLE public.textbook_lessons ALTER COLUMN event_id DROP NOT NULL"
    )
    op.execute(
        "ALTER TABLE public.textbook_lessons DROP CONSTRAINT IF EXISTS textbook_lessons_event_id_fkey"
    )

    # ── Clear existing textbook data to avoid conflicts ──
    op.execute("DELETE FROM public.textbook_lessons")
    op.execute("DELETE FROM public.textbook_parts")

    # ════════════════════════════════════════════════════════════
    # LỚP 12
    # ════════════════════════════════════════════════════════════
    op.execute("""
    INSERT INTO public.textbook_parts (id, grade_id, part_number, title, order_index) VALUES
      ('p-12-1','grade-12',1,'Thế giới trong và sau Chiến tranh lạnh',1),
      ('p-12-2','grade-12',2,'ASEAN: Những chặng đường lịch sử',2),
      ('p-12-3','grade-12',3,'Cách mạng tháng Tám năm 1945, chiến tranh giải phóng dân tộc và chiến tranh bảo vệ Tổ quốc trong lịch sử Việt Nam (từ tháng 8 năm 1945 đến nay)',3),
      ('p-12-4','grade-12',4,'Công cuộc Đổi mới ở Việt Nam từ năm 1986 đến nay',4),
      ('p-12-5','grade-12',5,'Lịch sử đối ngoại của Việt Nam thời cận – hiện đại',5),
      ('p-12-6','grade-12',6,'Hồ Chí Minh trong lịch sử Việt Nam',6)
    ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, order_index=EXCLUDED.order_index;
    """)

    op.execute("""
    INSERT INTO public.textbook_lessons (id, part_id, event_id, lesson_number, title, order_index) VALUES
      ('l-12-1','p-12-1',NULL,1,'Liên hợp quốc',1),
      ('l-12-2','p-12-1',NULL,2,'Trật tự thế giới trong Chiến tranh lạnh',2),
      ('l-12-3','p-12-1',NULL,3,'Trật tự thế giới sau Chiến tranh lạnh',3),
      ('l-12-4','p-12-2',NULL,4,'Sự ra đời và phát triển của Hiệp hội các quốc gia Đông Nam Á (ASEAN)',4),
      ('l-12-5','p-12-2',NULL,5,'Cộng đồng ASEAN: Từ ý tưởng đến hiện thực',5),
      ('l-12-6','p-12-3',NULL,6,'Cách mạng tháng Tám năm 1945',6),
      ('l-12-7','p-12-3',NULL,7,'Cuộc kháng chiến chống thực dân Pháp (1945 – 1954)',7),
      ('l-12-8','p-12-3',NULL,8,'Cuộc kháng chiến chống Mỹ, cứu nước (1954 – 1975)',8),
      ('l-12-9','p-12-3',NULL,9,'Đấu tranh bảo vệ Tổ quốc từ sau tháng 4 – 1975 đến nay. Một số bài học lịch sử của các cuộc kháng chiến bảo vệ Tổ quốc từ năm 1945 đến nay',9),
      ('l-12-10','p-12-4',NULL,10,'Khái quát về công cuộc Đổi mới từ năm 1986 đến nay',10),
      ('l-12-11','p-12-4',NULL,11,'Thành tựu cơ bản và bài học của công cuộc Đổi mới ở Việt Nam từ năm 1986 đến nay',11),
      ('l-12-12','p-12-5',NULL,12,'Hoạt động đối ngoại của Việt Nam trong đấu tranh giành độc lập dân tộc (đầu thế kỉ XX đến Cách mạng tháng Tám năm 1945)',12),
      ('l-12-13','p-12-5',NULL,13,'Hoạt động đối ngoại của Việt Nam từ sau Cách mạng tháng Tám năm 1945 đến nay',13),
      ('l-12-14','p-12-6',NULL,14,'Khái quát về cuộc đời và sự nghiệp của Hồ Chí Minh',14),
      ('l-12-15','p-12-6',NULL,15,'Hồ Chí Minh – Anh hùng Giải phóng dân tộc',15),
      ('l-12-16','p-12-6',NULL,16,'Dấu ấn Hồ Chí Minh trong lòng nhân dân thế giới và Việt Nam',16)
    ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, order_index=EXCLUDED.order_index;
    """)

    # ════════════════════════════════════════════════════════════
    # LỚP 9
    # ════════════════════════════════════════════════════════════
    op.execute("""
    INSERT INTO public.textbook_parts (id, grade_id, part_number, title, order_index) VALUES
      ('p-9-1','grade-9',1,'Thế giới từ năm 1918 đến năm 1945',1),
      ('p-9-2','grade-9',2,'Việt Nam từ năm 1918 đến năm 1945',2),
      ('p-9-3','grade-9',3,'Thế giới từ năm 1945 đến năm 1991',3),
      ('p-9-4','grade-9',4,'Việt Nam từ năm 1945 đến năm 1991',4),
      ('p-9-5','grade-9',5,'Thế giới từ năm 1991 đến nay',5),
      ('p-9-6','grade-9',6,'Việt Nam từ năm 1991 đến nay',6),
      ('p-9-7','grade-9',7,'Cách mạng khoa học, kĩ thuật và xu thế toàn cầu hoá',7)
    ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, order_index=EXCLUDED.order_index;
    """)

    op.execute("""
    INSERT INTO public.textbook_lessons (id, part_id, event_id, lesson_number, title, order_index) VALUES
      ('l-9-1','p-9-1',NULL,1,'Nước Nga và Liên Xô từ năm 1918 đến năm 1945',1),
      ('l-9-2','p-9-1',NULL,2,'Châu Âu và nước Mỹ từ năm 1918 đến năm 1945',2),
      ('l-9-3','p-9-1',NULL,3,'Châu Á từ năm 1918 đến năm 1945',3),
      ('l-9-4','p-9-1',NULL,4,'Chiến tranh thế giới thứ hai (1939 – 1945)',4),
      ('l-9-5','p-9-2',NULL,5,'Phong trào dân tộc dân chủ những năm 1918 – 1930',5),
      ('l-9-6','p-9-2',NULL,6,'Hoạt động của Nguyễn Ái Quốc và sự thành lập Đảng Cộng sản Việt Nam',6),
      ('l-9-7','p-9-2',NULL,7,'Phong trào cách mạng Việt Nam thời kì 1930 – 1939',7),
      ('l-9-8','p-9-2',NULL,8,'Cách mạng tháng Tám năm 1945',8),
      ('l-9-9','p-9-3',NULL,9,'Chiến tranh lạnh (1947 – 1989)',9),
      ('l-9-10','p-9-3',NULL,10,'Liên Xô và các nước Đông Âu từ năm 1945 đến năm 1991',10),
      ('l-9-11','p-9-3',NULL,11,'Nước Mỹ và các nước Tây Âu từ năm 1945 đến năm 1991',11),
      ('l-9-12','p-9-3',NULL,12,'Mỹ La-tinh từ năm 1945 đến năm 1991',12),
      ('l-9-13','p-9-3',NULL,13,'Một số nước ở châu Á từ năm 1945 đến năm 1991',13),
      ('l-9-14','p-9-4',NULL,14,'Xây dựng và bảo vệ chính quyền Việt Nam Dân chủ Cộng hoà (từ tháng 9 – 1945 đến tháng 12 – 1946)',14),
      ('l-9-15','p-9-4',NULL,15,'Những năm đầu Việt Nam kháng chiến chống thực dân Pháp xâm lược (1946 – 1950)',15),
      ('l-9-16','p-9-4',NULL,16,'Cuộc kháng chiến chống thực dân Pháp kết thúc thắng lợi (1951 – 1954)',16),
      ('l-9-17','p-9-4',NULL,17,'Việt Nam từ năm 1954 đến năm 1965',17),
      ('l-9-18','p-9-4',NULL,18,'Việt Nam từ năm 1965 đến năm 1975',18),
      ('l-9-19','p-9-4',NULL,19,'Việt Nam từ năm 1976 đến năm 1991',19),
      ('l-9-20','p-9-5',NULL,20,'Trật tự thế giới mới từ năm 1991 đến nay',20),
      ('l-9-21','p-9-5',NULL,21,'Liên bang Nga và nước Mỹ từ năm 1991 đến nay',21),
      ('l-9-22','p-9-5',NULL,22,'Châu Á từ năm 1991 đến nay',22),
      ('l-9-23','p-9-6',NULL,23,'Công cuộc Đổi mới từ năm 1991 đến nay',23),
      ('l-9-24','p-9-7',NULL,24,'Cách mạng khoa học, kĩ thuật và xu thế toàn cầu hoá',24)
    ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, order_index=EXCLUDED.order_index;
    """)

    # ════════════════════════════════════════════════════════════
    # LỚP 11
    # ════════════════════════════════════════════════════════════
    op.execute("""
    INSERT INTO public.textbook_parts (id, grade_id, part_number, title, order_index) VALUES
      ('p-11-1','grade-11',1,'Cách mạng tư sản và sự phát triển của chủ nghĩa tư bản',1),
      ('p-11-2','grade-11',2,'Chủ nghĩa xã hội từ năm 1917 đến nay',2),
      ('p-11-3','grade-11',3,'Quá trình giành độc lập của các quốc gia ở Đông Nam Á',3),
      ('p-11-4','grade-11',4,'Chiến tranh bảo vệ Tổ quốc và chiến tranh giải phóng dân tộc trong lịch sử Việt Nam (trước Cách mạng tháng Tám năm 1945)',4),
      ('p-11-5','grade-11',5,'Một số cuộc cải cách lớn trong lịch sử Việt Nam (trước năm 1858)',5),
      ('p-11-6','grade-11',6,'Lịch sử bảo vệ chủ quyền, các quyền và lợi ích hợp pháp của Việt Nam ở Biển Đông',6)
    ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, order_index=EXCLUDED.order_index;
    """)

    op.execute("""
    INSERT INTO public.textbook_lessons (id, part_id, event_id, lesson_number, title, order_index) VALUES
      ('l-11-1','p-11-1',NULL,1,'Một số vấn đề chung về cách mạng tư sản',1),
      ('l-11-2','p-11-1',NULL,2,'Sự xác lập và phát triển của chủ nghĩa tư bản',2),
      ('l-11-3','p-11-2',NULL,3,'Liên bang Cộng hoà xã hội chủ nghĩa Xô viết ra đời và sự phát triển của chủ nghĩa xã hội sau Chiến tranh thế giới thứ hai',3),
      ('l-11-4','p-11-2',NULL,4,'Chủ nghĩa xã hội từ năm 1991 đến nay',4),
      ('l-11-5','p-11-3',NULL,5,'Quá trình xâm lược và cai trị của chủ nghĩa thực dân ở Đông Nam Á',5),
      ('l-11-6','p-11-3',NULL,6,'Hành trình đi đến độc lập dân tộc ở Đông Nam Á',6),
      ('l-11-7','p-11-4',NULL,7,'Chiến tranh bảo vệ Tổ quốc trong lịch sử Việt Nam (trước năm 1945)',7),
      ('l-11-8','p-11-4',NULL,8,'Một số cuộc khởi nghĩa và chiến tranh giải phóng trong lịch sử Việt Nam (từ thế kỉ III TCN – đến cuối thế kỉ XIX)',8),
      ('l-11-9','p-11-5',NULL,9,'Cuộc cải cách của Hồ Quý Ly và triều Hồ',9),
      ('l-11-10','p-11-5',NULL,10,'Cuộc cải cách của Lê Thánh Tông (thế kỉ XV)',10),
      ('l-11-11','p-11-5',NULL,11,'Cuộc cải cách của Minh Mạng (nửa đầu thế kỉ XIX)',11),
      ('l-11-12','p-11-6',NULL,12,'Vị trí và tầm quan trọng của Biển Đông',12),
      ('l-11-13','p-11-6',NULL,13,'Việt Nam và Biển Đông',13)
    ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, order_index=EXCLUDED.order_index;
    """)

    # ════════════════════════════════════════════════════════════
    # LỚP 10
    # ════════════════════════════════════════════════════════════
    op.execute("""
    INSERT INTO public.textbook_parts (id, grade_id, part_number, title, order_index) VALUES
      ('p-10-1','grade-10',1,'Lịch sử và sử học, vai trò của sử học',1),
      ('p-10-2','grade-10',2,'Một số nền văn minh thế giới thời kì cổ – trung đại',2),
      ('p-10-3','grade-10',3,'Các cuộc cách mạng công nghiệp trong lịch sử thế giới',3),
      ('p-10-4','grade-10',4,'Văn minh Đông Nam Á cổ – trung đại',4),
      ('p-10-5','grade-10',5,'Một số nền văn minh trên đất nước Việt Nam (trước năm 1858)',5),
      ('p-10-6','grade-10',6,'Cộng đồng các dân tộc Việt Nam',6)
    ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, order_index=EXCLUDED.order_index;
    """)

    op.execute("""
    INSERT INTO public.textbook_lessons (id, part_id, event_id, lesson_number, title, order_index) VALUES
      ('l-10-1','p-10-1',NULL,1,'Hiện thực lịch sử và nhận thức lịch sử',1),
      ('l-10-2','p-10-1',NULL,2,'Tri thức lịch sử và cuộc sống',2),
      ('l-10-3','p-10-1',NULL,3,'Sử học với các lĩnh vực khoa học khác',3),
      ('l-10-4','p-10-1',NULL,4,'Sử học với một số lĩnh vực, ngành nghề hiện đại',4),
      ('l-10-5','p-10-2',NULL,5,'Khái quát lịch sử văn minh thế giới cổ – trung đại',5),
      ('l-10-6','p-10-2',NULL,6,'Văn minh Ai Cập cổ đại',6),
      ('l-10-7','p-10-2',NULL,7,'Văn minh Trung Hoa cổ – trung đại',7),
      ('l-10-8','p-10-2',NULL,8,'Văn minh Ấn Độ cổ – trung đại',8),
      ('l-10-9','p-10-2',NULL,9,'Văn minh Hy Lạp – La Mã cổ đại',9),
      ('l-10-10','p-10-2',NULL,10,'Văn minh Tây Âu thời Phục hưng',10),
      ('l-10-11','p-10-3',NULL,11,'Các cuộc Cách mạng công nghiệp thời kì cận đại',11),
      ('l-10-12','p-10-3',NULL,12,'Các cuộc Cách mạng công nghiệp thời kì hiện đại',12),
      ('l-10-13','p-10-4',NULL,13,'Cơ sở hình thành văn minh Đông Nam Á thời cổ – trung đại',13),
      ('l-10-14','p-10-4',NULL,14,'Hành trình phát triển và thành tựu văn minh Đông Nam Á thời cổ – trung đại',14),
      ('l-10-15','p-10-5',NULL,15,'Văn minh Văn Lang – Âu Lạc',15),
      ('l-10-16','p-10-5',NULL,16,'Văn minh Chăm-pa',16),
      ('l-10-17','p-10-5',NULL,17,'Văn minh Phù Nam',17),
      ('l-10-18','p-10-5',NULL,18,'Văn minh Đại Việt',18),
      ('l-10-19','p-10-6',NULL,19,'Các dân tộc trên đất nước Việt Nam',19),
      ('l-10-20','p-10-6',NULL,20,'Khối đại đoàn kết dân tộc Việt Nam',20)
    ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, order_index=EXCLUDED.order_index;
    """)

    # ════════════════════════════════════════════════════════════
    # LỚP 8
    # ════════════════════════════════════════════════════════════
    op.execute("""
    INSERT INTO public.textbook_parts (id, grade_id, part_number, title, order_index) VALUES
      ('p-8-1','grade-8',1,'Châu Âu và Bắc Mỹ từ nửa sau thế kỉ XVI đến thế kỉ XVIII',1),
      ('p-8-2','grade-8',2,'Đông Nam Á từ nửa sau thế kỉ XVI đến thế kỉ XIX',2),
      ('p-8-3','grade-8',3,'Việt Nam từ đầu thế kỉ XVI đến thế kỉ XVIII',3),
      ('p-8-4','grade-8',4,'Châu Âu và nước Mỹ từ cuối thế kỉ XVIII đến đầu thế kỉ XX',4),
      ('p-8-5','grade-8',5,'Châu Á từ nửa sau thế kỉ XIX đến đầu thế kỉ XX',5),
      ('p-8-6','grade-8',6,'Việt Nam từ thế kỉ XIX đến đầu thế kỉ XX',6)
    ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, order_index=EXCLUDED.order_index;
    """)

    op.execute("""
    INSERT INTO public.textbook_lessons (id, part_id, event_id, lesson_number, title, order_index) VALUES
      ('l-8-1','p-8-1',NULL,1,'Các cuộc cách mạng tư sản ở châu Âu và Bắc Mỹ',1),
      ('l-8-2','p-8-1',NULL,2,'Cách mạng công nghiệp',2),
      ('l-8-3','p-8-2',NULL,3,'Tình hình Đông Nam Á từ nửa sau thế kỉ XVI đến thế kỉ XIX',3),
      ('l-8-4','p-8-3',NULL,4,'Xung đột Nam – Bắc triều và Trịnh – Nguyễn',4),
      ('l-8-5','p-8-3',NULL,5,'Quá trình khai phá vùng đất phía Nam từ thế kỉ XVI đến thế kỉ XVIII',5),
      ('l-8-6','p-8-3',NULL,6,'Kinh tế, văn hoá và tôn giáo ở Đại Việt trong các thế kỉ XVI – XVIII',6),
      ('l-8-7','p-8-3',NULL,7,'Khởi nghĩa nông dân ở Đàng Ngoài thế kỉ XVIII',7),
      ('l-8-8','p-8-3',NULL,8,'Phong trào Tây Sơn',8),
      ('l-8-9','p-8-4',NULL,9,'Các nước Anh, Pháp, Đức, Mỹ chuyển sang giai đoạn chủ nghĩa đế quốc',9),
      ('l-8-10','p-8-4',NULL,10,'Công xã Pa-ri (năm 1871)',10),
      ('l-8-11','p-8-4',NULL,11,'Phong trào công nhân và sự ra đời của chủ nghĩa Mác',11),
      ('l-8-12','p-8-4',NULL,12,'Chiến tranh thế giới thứ nhất (1914 – 1918)',12),
      ('l-8-13','p-8-4',NULL,13,'Cách mạng tháng Mười Nga năm 1917',13),
      ('l-8-14','p-8-4',NULL,14,'Sự phát triển của khoa học, kĩ thuật, văn học, nghệ thuật trong các thế kỉ XVIII – XIX',14),
      ('l-8-15','p-8-5',NULL,15,'Trung Quốc',15),
      ('l-8-16','p-8-5',NULL,16,'Nhật Bản',16),
      ('l-8-17','p-8-5',NULL,17,'Ấn Độ',17),
      ('l-8-18','p-8-5',NULL,18,'Đông Nam Á',18),
      ('l-8-19','p-8-6',NULL,19,'Việt Nam nửa đầu thế kỉ XIX',19),
      ('l-8-20','p-8-6',NULL,20,'Cuộc kháng chiến chống thực dân Pháp xâm lược của nhân dân Việt Nam (1858 – 1884)',20),
      ('l-8-21','p-8-6',NULL,21,'Phong trào chống Pháp của nhân dân Việt Nam trong những năm cuối thế kỉ XIX',21),
      ('l-8-22','p-8-6',NULL,22,'Trào lưu cải cách ở Việt Nam nửa cuối thế kỉ XIX',22),
      ('l-8-23','p-8-6',NULL,23,'Việt Nam đầu thế kỉ XX',23)
    ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, order_index=EXCLUDED.order_index;
    """)


def downgrade() -> None:
    op.execute("DELETE FROM public.textbook_lessons WHERE id LIKE 'l-8-%' OR id LIKE 'l-9-%' OR id LIKE 'l-10-%' OR id LIKE 'l-11-%' OR id LIKE 'l-12-%'")
    op.execute("DELETE FROM public.textbook_parts WHERE id LIKE 'p-8-%' OR id LIKE 'p-9-%' OR id LIKE 'p-10-%' OR id LIKE 'p-11-%' OR id LIKE 'p-12-%'")
