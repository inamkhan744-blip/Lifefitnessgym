# printer_utils.py - Replit/Linux version
import os
import subprocess
import tempfile
from datetime import datetime
import uuid

class ReceiptPrinter:
    def __init__(self, printer_name="BC-87AC"):
        self.printer_name = printer_name
    
    def _check_printer(self):
        """Check if printer is available on Linux"""
        try:
            # Check CUPS printers
            result = subprocess.run(
                ['lpstat', '-p', '-d'],
                capture_output=True, text=True, timeout=5
            )
            if 'printer' in result.stdout.lower():
                return True
            
            # Check USB devices
            result = subprocess.run(
                ['ls', '/dev/usb/lp*'],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _send_raw(self, raw_data):
        """Send raw ESC/POS data to printer"""
        temp_file = None
        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
                f.write(raw_data)
                temp_file = f.name
            
            # Method 1: CUPS raw
            try:
                result = subprocess.run([
                    'lp', '-d', self.printer_name,
                    '-o', 'raw',
                    temp_file
                ], capture_output=True, timeout=10)
                if result.returncode == 0:
                    return True
            except:
                pass
            
            # Method 2: Direct USB
            try:
                for device in ['/dev/usb/lp0', '/dev/usb/lp1', '/dev/ttyUSB0', '/dev/ttyUSB1']:
                    if os.path.exists(device):
                        with open(device, 'wb') as f:
                            f.write(raw_data)
                        return True
            except:
                pass
            
            # Method 3: lpr fallback
            try:
                result = subprocess.run([
                    'lpr', '-P', self.printer_name,
                    temp_file
                ], capture_output=True, timeout=10)
                return result.returncode == 0
            except:
                pass
            
            return False
            
        except Exception as e:
            print(f"Print error: {e}")
            return False
        finally:
            try:
                if temp_file and os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
    
    def _build_receipt(self, data, copy_type="MEMBER COPY"):
        """Build receipt content with ESC/POS commands"""
        receipt_no = data.get('receipt_no', f"RCP-{uuid.uuid4().hex[:6].upper()}")
        current_time = datetime.now().strftime('%I:%M %p')
        
        lines = [
            "=" * 40,
            f"{data.get('gym_name', 'FITNESS PRO'):^40}",
            "🏋️ GYM & FITNESS CENTER",
            "",
            f"📍 {data.get('gym_address', 'Your Gym Address')}",
            f"📞 {data.get('gym_phone', '+92-XXX-XXXXXXX')}",
            "-" * 40,
            "",
            f"📋 {copy_type}",
            f"RECEIPT #: {receipt_no}",
            f"DATE: {data.get('date', datetime.now().strftime('%Y-%m-%d'))}",
            f"TIME: {current_time}",
            f"COLLECTED BY: {data.get('collected_by', 'Staff')}",
            "",
            "─── MEMBER DETAILS ───",
            f"Name: {data.get('member_name', 'N/A')}",
            f"Serial: {data.get('serial', 'N/A')}",
            f"Phone: {data.get('phone', 'N/A')}",
            "",
            "─── PAYMENT DETAILS ───",
            f"Amount: PKR {data.get('amount', 0):,.2f}",
            f"Method: {data.get('method', 'Cash')}",
            "Status: ✅ PAID",
            "",
            "─── MEMBERSHIP ───",
            f"Valid From: {data.get('period_start', 'N/A')}",
            f"Valid Till: {data.get('period_end', 'N/A')}",
            "",
            "=" * 40,
            "",
            "💪 Thank you! Keep this copy." if copy_type == "MEMBER COPY" else "🏢 GYM OFFICE COPY",
            "=" * 40,
            "",
        ]
        return lines
    
    def print_dual_copies(self, data):
        """Print 2 copies"""
        data['receipt_no'] = data.get('receipt_no', f"RCP-{uuid.uuid4().hex[:6].upper()}")
        
        # ESC/POS commands
        init = b'\x1B\x40'
        align_center = b'\x1B\x61\x01'
        cut = b'\x1B\x6D'
        
        raw_data = init + align_center
        
        # Member copy
        for line in self._build_receipt(data, "MEMBER COPY"):
            raw_data += (line + "\n").encode('utf-8')
        raw_data += cut + b'\x0C'
        
        # Gym copy
        for line in self._build_receipt(data, "GYM COPY"):
            raw_data += (line + "\n").encode('utf-8')
        raw_data += cut
        
        return self._send_raw(raw_data)
    
    def print_single_copy(self, data):
        """Print single copy"""
        data['receipt_no'] = data.get('receipt_no', f"RCP-{uuid.uuid4().hex[:6].upper()}")
        
        init = b'\x1B\x40'
        align_center = b'\x1B\x61\x01'
        cut = b'\x1B\x6D'
        
        raw_data = init + align_center
        for line in self._build_receipt(data, "MEMBER COPY"):
            raw_data += (line + "\n").encode('utf-8')
        raw_data += cut
        
        return self._send_raw(raw_data)
    
    def test_print(self):
        """Test print"""
        init = b'\x1B\x40'
        align_center = b'\x1B\x61\x01'
        cut = b'\x1B\x6D'
        
        lines = [
            "=" * 40,
            "TEST PRINT",
            "",
            "🖨️ Printer is working correctly!",
            "✅ Connection successful",
            "",
            f"Date: {datetime.now().strftime('%Y-%m-%d')}",
            f"Time: {datetime.now().strftime('%I:%M %p')}",
            "",
            "=" * 40,
        ]
        
        raw_data = init + align_center
        for line in lines:
            raw_data += (line + "\n").encode('utf-8')
        raw_data += cut
        
        return self._send_raw(raw_data)

# Global instance
_printer = None

def get_printer():
    global _printer
    if _printer is None:
        _printer = ReceiptPrinter()
    return _printer