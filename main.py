import sys
import ipaddress
import asyncio
import ssl
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, QProgressBar, QMessageBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)
from qasync import QEventLoop, asyncSlot

class AsyncScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("hokyahhhh :v")
        self.resize(850, 650)
        
        self.is_scanning = False
        self.scan_task = None
        self.scanned_count = 0
        self.open_ports_count = 0
        
        self.apply_modern_style()
        self.init_ui()
        
    def apply_modern_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QWidget { color: #cdd6f4; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
            
            QGroupBox { 
                color: #89b4fa; 
                font-weight: bold; 
                border: 1px solid #45475a; 
                border-radius: 6px; 
                margin-top: 12px; 
                padding-top: 10px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            
            QLineEdit, QComboBox { 
                background-color: #313244; 
                border: 1px solid #45475a; 
                border-radius: 4px; 
                padding: 6px; 
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #89b4fa; }
            
            QPushButton { border-radius: 5px; padding: 8px 12px; font-weight: bold; }
            QPushButton#btnStart { background-color: #a6e3a1; color: #11111b; }
            QPushButton#btnStart:hover { background-color: #94e2a4; }
            QPushButton#btnStart:disabled { background-color: #45475a; color: #7f849c; }
            
            QPushButton#btnStop { background-color: #f38ba8; color: #11111b; }
            QPushButton#btnStop:hover { background-color: #f59aab; }
            QPushButton#btnStop:disabled { background-color: #45475a; color: #7f849c; }
            
            QTableWidget { 
                background-color: #181825; 
                alternate-background-color: #1e1e2e;
                gridline-color: #313244; 
                border: 1px solid #45475a; 
                border-radius: 6px;
                color: #a6e3a1; 
            }
            QHeaderView::section { 
                background-color: #313244; 
                color: #cdd6f4; 
                padding: 6px; 
                border: none;
                border-right: 1px solid #45475a;
                border-bottom: 1px solid #45475a;
                font-weight: bold;
            }
            
            QProgressBar { 
                text-align: center; 
                background-color: #313244; 
                border: 1px solid #45475a; 
                border-radius: 4px; 
                color: #cdd6f4;
                font-weight: bold;
            }
            QProgressBar::chunk { background-color: #89b4fa; border-radius: 3px; }
            
            QTextEdit { 
                background-color: #181825; 
                border: 1px solid #45475a; 
                border-radius: 6px; 
                font-family: Consolas, Monaco, monospace;
            }
        """)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        
        config_layout = QHBoxLayout()
        
        grp_target = QGroupBox("1. Konfigurasi Jaringan")
        lay_target = QVBoxLayout(grp_target)
        
        row1_target = QHBoxLayout()
        row1_target.addWidget(QLabel("IP / Network:"))
        self.ip_input = QLineEdit("10.0.0.0")
        row1_target.addWidget(self.ip_input)
        
        row1_target.addWidget(QLabel("Subnet:"))
        self.mask_combobox = QComboBox()
        self.mask_combobox.addItems(["/24", "/16", "/8", "Custom"])
        self.mask_combobox.currentIndexChanged.connect(self.handle_mask_change)
        row1_target.addWidget(self.mask_combobox)
        lay_target.addLayout(row1_target)
        
        row2_target = QHBoxLayout()
        row2_target.addWidget(QLabel("Target Port:"))
        self.port_input = QLineEdit("80")
        row2_target.addWidget(self.port_input)
        lay_target.addLayout(row2_target)
        
        grp_engine = QGroupBox("2. Konfigurasi Mesin (Asyncio)")
        lay_engine = QVBoxLayout(grp_engine)
        
        row1_engine = QHBoxLayout()
        row1_engine.addWidget(QLabel("Max Simultan:"))
        self.limit_input = QLineEdit("300")  # Diturunkan sedikit untuk stabilitas OS
        row1_engine.addWidget(self.limit_input)
        
        row1_engine.addWidget(QLabel("Timeout (detik):"))
        self.timeout_input = QLineEdit("0.5")
        row1_engine.addWidget(self.timeout_input)
        lay_engine.addLayout(row1_engine)
        
        row2_engine = QHBoxLayout()
        row2_engine.addWidget(QLabel("Simpan ke File:"))
        self.file_input = QLineEdit("hasil_scan.txt")
        row2_engine.addWidget(self.file_input)
        lay_engine.addLayout(row2_engine)

        config_layout.addWidget(grp_target)
        config_layout.addWidget(grp_engine)
        main_layout.addLayout(config_layout)
        
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("🚀 Mulai Pemindaian")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.clicked.connect(self.start_scan_wrapper)
        btn_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("🛑 Batalkan")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_scan)
        btn_layout.addWidget(self.btn_stop)
        main_layout.addLayout(btn_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)
        
        splitter = QSplitter(Qt.Vertical)
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["No.", "IP Address", "Port", "Status URL"])
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setShowGrid(True)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        splitter.addWidget(self.result_table)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Log sistem dan ringkasan akan muncul di sini...")
        splitter.addWidget(self.log_output)
        
        splitter.setSizes([400, 150])
        main_layout.addWidget(splitter)
        
    def handle_mask_change(self):
        if "Custom" in self.mask_combobox.currentText():
            if "/" not in self.ip_input.text():
                self.ip_input.setText(self.ip_input.text() + "/24")
        else:
            current_ip = self.ip_input.text().split("/")[0]
            self.ip_input.setText(current_ip)

    def log(self, text):
        self.log_output.append(text)
        self.log_output.ensureCursorVisible()

    def add_table_row(self, ip, port, url):
        row_pos = self.result_table.rowCount()
        self.result_table.insertRow(row_pos)
        
        no_item = QTableWidgetItem(str(self.open_ports_count))
        no_item.setTextAlignment(Qt.AlignCenter)
        self.result_table.setItem(row_pos, 0, no_item)
        
        ip_item = QTableWidgetItem(ip)
        ip_item.setTextAlignment(Qt.AlignCenter)
        self.result_table.setItem(row_pos, 1, ip_item)
        
        port_item = QTableWidgetItem(str(port))
        port_item.setTextAlignment(Qt.AlignCenter)
        self.result_table.setItem(row_pos, 2, port_item)
        
        url_item = QTableWidgetItem(url)
        self.result_table.setItem(row_pos, 3, url_item)
        
        # UI Optimasi: Dihapus scrollToBottom dari sini agar tidak rendering berlebih.
        # Akan dieksekusi per-batch di process_done_tasks

    @asyncSlot()
    async def start_scan_wrapper(self):
        ip_text = self.ip_input.text().strip()
        mask_text = self.mask_combobox.currentText()
        cidr_target = ip_text if "Custom" in mask_text else f"{ip_text}{mask_text}"
        output_file = self.file_input.text().strip() or "hasil_scan.txt"

        try:
            port = int(self.port_input.text().strip())
            max_conn = int(self.limit_input.text().strip())
            timeout = float(self.timeout_input.text().strip())
            if not (1 <= port <= 65535): raise ValueError
        except ValueError:
            QMessageBox.critical(self, "Error Input", "Pastikan Port (1-65535), Max Conn, dan Timeout diisi angka valid!")
            return

        try:
            network = ipaddress.ip_network(cidr_target, strict=False)
            hosts_generator = network.hosts()
            total_ips = network.num_addresses - (2 if network.prefixlen < 31 else 0)
        except Exception as e:
            QMessageBox.critical(self, "Error Network", f"Format IP/Subnet salah: {str(e)}")
            return

        self.is_scanning = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        self.result_table.setRowCount(0)
        self.log_output.clear()
        self.progress_bar.setRange(0, total_ips)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Memindai: %v / %m IP (%p%)")
        self.progress_bar.show()
        
        self.scanned_count = 0
        self.open_ports_count = 0

        self.scan_task = asyncio.create_task(self.run_async_scanner(hosts_generator, total_ips, cidr_target, port, max_conn, timeout, output_file))
        try:
            await self.scan_task
        except asyncio.CancelledError:
            pass # Penanganan log diletakkan di run_async_scanner agar lebih akurat
        finally:
            self.reset_ui_state()

    async def _do_check(self, ip_str, port, timeout):
        """Fungsi helper terisolasi untuk memastikan penutupan resource socket secara ketat"""
        writer_tcp = None
        writer_ssl = None
        
        # 1. Cek Koneksi TCP Dasar
        try:
            reader, writer_tcp = await asyncio.wait_for(asyncio.open_connection(ip_str, port), timeout=timeout)
        except Exception:
            return None
        finally:
            # Cegah memory/file descriptor leak, pastikan selalu ditutup
            if writer_tcp:
                try:
                    writer_tcp.close()
                    await writer_tcp.wait_closed()
                except Exception:
                    pass

        # 2. Jika terbuka, coba deteksi HTTPS via SSL Handshake
        protocol = "http" 
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Pengecekan SSL dengan timeout terpisah
            r_ssl, writer_ssl = await asyncio.wait_for(
                asyncio.open_connection(ip_str, port, ssl=ctx), 
                timeout=timeout
            )
            protocol = "https"
        except Exception:
            # Abaikan semua error (timeout/SSL error), kembalikan sebagai HTTP biasa
            pass
        finally:
             # Bersihkan sisa koneksi SSL agar tidak menjadi thread zombie
             if writer_ssl:
                try:
                    writer_ssl.close()
                    await writer_ssl.wait_closed()
                except Exception:
                    pass
                
        return (ip_str, protocol)

    async def check_port_async(self, ip_str, port, timeout, semaphore):
        async with semaphore:
            if not self.is_scanning:
                return None
            
            try:
                # Menambahkan buffer waktu sedikit (timeout + 1) untuk memastikan Exception tertangkap
                return await asyncio.wait_for(self._do_check(ip_str, port, timeout), timeout=timeout + 1.0)
            except Exception:
                return None

    async def run_async_scanner(self, hosts_gen, total_ips, cidr, port, max_conn, timeout, output_file):
        start_time = datetime.now()

        self.log(f"[*] Target      : {cidr} ({total_ips:,} IP)")
        self.log(f"[*] Port Cek    : {port}")
        self.log(f"[*] Max Conn    : {max_conn} (Simultan)")
        self.log(f"[*] Memulai pemindaian...\n" + "-"*50)

        semaphore = asyncio.Semaphore(max_conn)
        tasks = set()
        
        try:
            with open(output_file, "w") as f:
                f.write(f"=== HASIL MASS SCAN ASYNC (PORT {port}) ===\n")

                for ip in hosts_gen:
                    if not self.is_scanning:
                        break
                    
                    task = asyncio.create_task(self.check_port_async(str(ip), port, timeout, semaphore))
                    tasks.add(task)
                    
                    if len(tasks) >= max_conn:
                        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                        tasks = pending
                        self.process_done_tasks(done, f, port)

                # Bersihkan sisa antrean tugas
                while tasks:
                    if not self.is_scanning:
                        break
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = pending
                    self.process_done_tasks(done, f, port)

                if not self.is_scanning:
                    self.log("\n[!] Sinyal batal diterima. Membersihkan antrean thread...")
                    for t in tasks:
                        t.cancel()
                else:
                    end_time = datetime.now()
                    duration = end_time - start_time
                    summary = (
                        f"\n" + "-" * 50 + "\n"
                        f"=== RINGKASAN ===\n"
                        f"Total IP Dipindai  : {self.scanned_count:,} / {total_ips:,}\n"
                        f"Port Terbuka       : {self.open_ports_count}\n"
                        f"Durasi Pemindaian  : {duration}\n"
                        f"Disimpan ke        : {output_file}\n"
                    )
                    self.log(summary)

        except asyncio.CancelledError:
            self.log("\n[!] Pemindaian dibatalkan paksa. Membersihkan resource...")
            for t in tasks:
                t.cancel()
            raise # Lemparkan kembali agar ditangkap oleh start_scan_wrapper
        except Exception as e:
            self.log(f"\n[!] Terjadi kesalahan sistem: {str(e)}")

    def process_done_tasks(self, done_tasks, file_handle, port):
        has_new_data = False
        
        for task in done_tasks:
            self.scanned_count += 1
            
            # Update Progress Bar
            if self.scanned_count % 100 == 0 or self.scanned_count == self.progress_bar.maximum():
                self.progress_bar.setValue(self.scanned_count)

            try:
                result = task.result()
                if result:
                    ip_res, protocol = result
                    self.open_ports_count += 1
                    url = f"{protocol}://{ip_res}:{port}"
                    self.add_table_row(ip_res, port, url)
                    
                    file_handle.write(url + "\n")
                    file_handle.flush()
                    has_new_data = True
            except Exception:
                pass
                
        # Scroll otomatis hanya jika ada data baru masuk di batch ini (menghindari lag UI)
        if has_new_data:
            self.result_table.scrollToBottom()

    def stop_scan(self):
        self.is_scanning = False
        if self.scan_task and not self.scan_task.done():
            self.scan_task.cancel()

    def reset_ui_state(self):
        self.is_scanning = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

if __name__ == "__main__":
    # Workaround untuk sistem operasi yang membatasi ProactorEventLoop policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    app = QApplication(sys.argv)
    
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = AsyncScannerApp()
    window.show()
    
    with loop:
        sys.exit(loop.run_forever())
