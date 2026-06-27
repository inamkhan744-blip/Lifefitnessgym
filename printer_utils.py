# printer_utils.py
import os
import subprocess
import tempfile
from datetime import datetime
import streamlit as st
import uuid

class ReceiptPrinter:
    def __init__(self, printer_name="BC-87AC"):
        self.printer_name = printer_name
        self._check_printer()
    
    def _check_printer(self):
        """Check if printer is available"""
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    ['wmic', 'printer', 'get', 'name'],
                    capture_output=True, text=True
                )
                if self.printer_name not in result.stdout:
                    # Try to find any thermal printer
                    for line in result.stdout.split('\n'):
                        if 'thermal' in line.lower() or 'pos' in line.lower() or '80mm' in line.lower():
                            self.printer_name = line.strip()
                            return True
                    return False
            return True
        except:
            return False
    
    def print_dual_copies(self, data):
        """Print 2 copies - Member copy and Gym copy"""
        
        receipt_no = data.get('receipt_no', f"RCP-{uuid.uuid4().hex[:6].upper()}")
        data['receipt_no'] = receipt_no
        
        # === MEMBER COPY ===
        member_receipt = f"""
╔═══════════════════════════════════════════════╗
║                  {data.get('gym_name', 'FITNESS PRO'):^40} ║
║              🏋️ GYM & FITNESS CENTER          ║
║                                               ║
║           📍 {data.get('gym_address', '123 Main St'):^33} ║
║           📞 {data.get('gym_phone', '+92-300-1234567'):^33} ║
║                                               ║
╠═══════════════════════════════════════════════╣
║                                               ║
║   📋 MEMBER COPY                              ║
║   RECEIPT #: {receipt_no:<27} ║
║   DATE: {data.get('date', datetime.now().strftime('%Y-%m-%d')):<30} ║
║   TIME: {data.get('time', datetime.now().strftime('%I:%M %p')):<30} ║
║   COLLECTED BY: {data.get('collected_by', 'Staff'):<23} ║
║                                               ║
║   ─── MEMBER DETAILS ───                      ║
║   Name: {data.get('member_name', 'N/A'):<32} ║
║   Serial: {data.get('serial', 'N/A'):<30}    ║
║   Phone: {data.get('phone', 'N/A'):<30}      ║
║                                               ║
║   ─── PAYMENT DETAILS ───                     ║
║   Amount: PKR {data.get('amount', 0):>14,.2f} ║
║   Method: {data.get('method', 'Cash'):<30}    ║
║   Status: ✅ PAID                             ║
║                                               ║
║   ─── MEMBERSHIP ───                         ║
║   Valid From: {data.get('period_start', 'N/A'):<24} ║
║   Valid Till: {data.get('period_end', 'N/A'):<26} ║
║                                               ║
╠═══════════════════════════════════════════════╣
║                                               ║
║          💪 Thank you for your payment!       ║
║          🏷️ KEEP THIS COPY WITH YOU          ║
║                                               ║
║      ════════════════════════════════          ║
║         Have a great workout! 🏋️             ║
╚═══════════════════════════════════════════════╝
"""

        # === GYM COPY ===
        gym_receipt = f"""
╔═══════════════════════════════════════════════╗
║                  {data.get('gym_name', 'FITNESS PRO'):^40} ║
║              🏋️ GYM & FITNESS CENTER          ║
║                                               ║
╠═══════════════════════════════════════════════╣
║                                               ║
║   📋 GYM COPY (OFFICE RECORD)                 ║
║   RECEIPT #: {receipt_no:<27} ║
║   DATE: {data.get('date', datetime.now().strftime('%Y-%m-%d')):<30} ║
║   TIME: {data.get('time', datetime.now().strftime('%I:%M %p')):<30} ║
║   COLLECTED BY: {data.get('collected_by', 'Staff'):<23} ║
║                                               ║
║   ─── MEMBER DETAILS ───                      ║
║   Name: {data.get('member_name', 'N/A'):<32} ║
║   Serial: {data.get('serial', 'N/A'):<30}    ║
║   Phone: {data.get('phone', 'N/A'):<30}      ║
║                                               ║
║   ─── PAYMENT DETAILS ───                     ║
║   Amount: PKR {data.get('amount', 0):>14,.2f} ║
║   Method: {data.get('method', 'Cash'):<30}    ║
║   Status: ✅ PAID                             ║
║                                               ║
║   ─── MEMBERSHIP ───                         ║
║   Valid From: {data.get('period_start', 'N/A'):<24} ║
║   Valid Till: {data.get('period_end', 'N/A'):<26} ║
║                                               ║
╠═══════════════════════════════════════════════╣
║                                               ║
║          🏢 GYM OFFICE COPY                   ║
║          Keep for record keeping              ║
║                                               ║
║      ════════════════════════════════          ║
║         Payment recorded in system            ║
╚═══════════════════════════════════════════════╝
"""

        # Print both copies
        success1 = self._send_to_printer(member_receipt)
        success2 = self._send_to_printer(gym_receipt)
        
        return success1 and success2
    
    def print_attendance(self, data):
        """Print attendance slip"""
        
        slip = f"""
╔═══════════════════════════════════════════════╗
║                  {data.get('gym_name', 'FITNESS PRO'):^40} ║
║              🏋️ GYM & FITNESS CENTER          ║
║                                               ║
╠═══════════════════════════════════════════════╣
║                                               ║
║   📋 ATTENDANCE SLIP                          ║
║                                               ║
║   Member: {data.get('member_name', 'N/A'):<29} ║
║   Serial: {data.get('serial', 'N/A'):<30}    ║
║   Date: {data.get('date', datetime.now().strftime('%Y-%m-%d')):<30} ║
║   Time: {data.get('time', datetime.now().strftime('%I:%M %p')):<30} ║
║   Status: ✅ CHECKED IN                       ║
║                                               ║
║                                               ║
║          ✅ Welcome to the gym!               ║
║          💪 Have a great workout!             ║
║                                               ║
╚═══════════════════════════════════════════════╝
"""
        return self._send_to_printer(slip)
    
    def _send_to_printer(self, content):
        """Send content to printer"""
        try:
            if os.name == 'nt':  # Windows
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    f.write(content)
                    temp_file = f.name
                
                # Print using Notepad
                result = subprocess.run([
                    'notepad', '/p', temp_file
                ], capture_output=True, timeout=10)
                
                os.unlink(temp_file)
                return result.returncode == 0
            else:  # Linux/Mac
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    f.write(content)
                    temp_file = f.name
                
                result = subprocess.run([
                    'lp', '-d', self.printer_name, temp_file
                ], capture_output=True, timeout=10)
                
                os.unlink(temp_file)
                return result.returncode == 0
        except Exception as e:
            print(f"Print error: {e}")
            return False

    def test_print(self):
        """Test print to check printer connection"""
        test_receipt = """
╔═══════════════════════════════════════════════╗
║                 TEST PRINT                    ║
║                                               ║
║   🖨️ Printer is working correctly!            ║
║   ✅ Connection successful                    ║
║                                               ║
║   Date: {0}                                   ║
║   Time: {1}                                   ║
║                                               ║
║   ════════════════════════════════             ║
║         Print test successful!                ║
╚═══════════════════════════════════════════════╝
""".format(datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%I:%M %p'))
        
        return self._send_to_printer(test_receipt)

# Global printer instance
_printer = None

def get_printer():
    global _printer
    if _printer is None:
        _printer = ReceiptPrinter()
    return _printer