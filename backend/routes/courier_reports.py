"""
Courier Reports & Profile Management
Phase 1: PDF Reports, Profile Update, Availability, Order History
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from auth_cookie import get_current_user_from_cookie_or_bearer

router = APIRouter(prefix="/courier", tags=["courier-reports"])

# === AUTHENTICATION HELPER ===

async def get_courier_user(current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Get current courier user with role validation"""
    if current_user.get("role") != "courier":
        raise HTTPException(
            status_code=403,
            detail="Courier access required"
        )
    return current_user

# === MODELS ===

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    iban: Optional[str] = None
    vehicleType: Optional[str] = None
    plate: Optional[str] = None
    
    @validator('iban')
    def validate_iban(cls, v):
        if v and not v.startswith('TR'):
            # Auto-add TR prefix if missing
            v = 'TR' + v
        if v and len(v) != 26:
            raise ValueError('Turkish IBAN must be 26 characters (TR + 24 digits)')
        return v

class AvailabilitySlot(BaseModel):
    weekday: int  # 0-6 (Monday-Sunday)
    start: str  # "HH:mm"
    end: str  # "HH:mm"
    
    @validator('weekday')
    def validate_weekday(cls, v):
        if v < 0 or v > 6:
            raise ValueError('weekday must be between 0-6')
        return v

class AvailabilityRequest(BaseModel):
    slots: List[AvailabilitySlot]

# === PDF GENERATION ===

def create_earnings_pdf(courier_data: Dict, earnings_data: List[Dict], date_range: str, from_date: str, to_date: str) -> BytesIO:
    """Generate PDF earnings report with Turkish character support"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    # Use default fonts that support Unicode
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a202c'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4a5568')
    )
    
    elements = []
    
    # Title
    title = Paragraph(f"KURYE KAZANÇ RAPORU - {date_range.upper()}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))
    
    # Courier Info
    courier_info = [
        ['Kurye Bilgileri', ''],
        ['Ad Soyad:', f"{courier_data.get('name', '')} {courier_data.get('surname', '')}"],
        ['Email:', courier_data.get('email', '')],
        ['Telefon:', courier_data.get('phone', '')],
        ['Rapor Tarihi:', f"{from_date} - {to_date}"]
    ]
    
    info_table = Table(courier_info, colWidths=[5*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#4299e1')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 1*cm))
    
    # Check if earnings data exists
    if not earnings_data:
        no_data_text = Paragraph(
            "<b>Bu dönem için kazanç verisi bulunmamaktadır.</b><br/><br/>"
            "Henüz teslim edilmiş sipariş bulunmuyor.",
            normal_style
        )
        elements.append(no_data_text)
    else:
        # Summary Statistics
        total_deliveries = len(earnings_data)
        total_earnings = sum(e['amount'] for e in earnings_data)
        avg_earning = total_earnings / total_deliveries if total_deliveries > 0 else 0
        
        summary = Paragraph(f"<b>ÖZET</b>", header_style)
        elements.append(summary)
        
        summary_data = [
            ['Toplam Teslimat', 'Toplam Kazanç', 'Ortalama Kazanç'],
            [f"{total_deliveries} adet", f"₺{total_earnings:.2f}", f"₺{avg_earning:.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[5*cm, 5*cm, 5*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#48bb78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fff4')),
            ('FONTSIZE', (0, 1), (-1, -1), 14),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#9ae6b4'))
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 1*cm))
        
        # Detailed Breakdown by Business
        business_breakdown = {}
        for earning in earnings_data:
            business_name = earning.get('business_name', 'Bilinmiyor')
            if business_name not in business_breakdown:
                business_breakdown[business_name] = {'count': 0, 'total': 0}
            business_breakdown[business_name]['count'] += 1
            business_breakdown[business_name]['total'] += earning['amount']
        
        breakdown_header = Paragraph(f"<b>İŞLETME BAZINDA KAZANÇLAR</b>", header_style)
        elements.append(breakdown_header)
        
        breakdown_data = [['İşletme Adı', 'Teslimat', 'Toplam Kazanç']]
        for business_name, data in business_breakdown.items():
            breakdown_data.append([
                business_name,
                f"{data['count']} adet",
                f"₺{data['total']:.2f}"
            ])
        
        breakdown_table = Table(breakdown_data, colWidths=[8*cm, 3.5*cm, 3.5*cm])
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#faf5ff')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#faf5ff'), colors.HexColor('#f3e8ff')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d6bcfa'))
        ]))
        
        elements.append(breakdown_table)
        elements.append(Spacer(1, 1*cm))
        
        # Detailed Transactions
        if len(earnings_data) <= 50:  # Only show detailed list for reasonable number of orders
            detail_header = Paragraph(f"<b>DETAYLI SİPARİŞ LİSTESİ</b>", header_style)
            elements.append(detail_header)
            
            detail_data = [['Tarih', 'İşletme', 'Sipariş No', 'Kazanç']]
            for earning in sorted(earnings_data, key=lambda x: x['created_at'], reverse=True):
                created_at = earning['created_at']
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        pass
                date_str = created_at.strftime('%d/%m/%Y %H:%M') if isinstance(created_at, datetime) else str(created_at)
                
                detail_data.append([
                    date_str,
                    earning.get('business_name', 'N/A')[:20],
                    earning.get('order_id', 'N/A')[:12],
                    f"₺{earning['amount']:.2f}"
                ])
            
            detail_table = Table(detail_data, colWidths=[4*cm, 5*cm, 3.5*cm, 2.5*cm])
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ed8936')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fffaf0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fffaf0'), colors.HexColor('#feebc8')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fbd38d'))
            ]))
            
            elements.append(detail_table)
    
    # Footer
    elements.append(Spacer(1, 1.5*cm))
    footer_text = Paragraph(
        f"<i>Bu rapor {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} tarihinde Kuryecini sistemi tarafından oluşturulmuştur.</i>",
        ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.HexColor('#a0aec0'), alignment=TA_RIGHT)
    )
    elements.append(footer_text)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# === ENDPOINTS ===

@router.get("/earnings/report/pdf")
async def get_earnings_pdf(
    range: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_courier_user)
):
    """
    Generate PDF earnings report for courier
    
    Range: daily, weekly, monthly
    from_date/to_date: YYYY-MM-DD format (optional, auto-calculated if not provided)
    """
    try:
        from server import db
        
        courier_id = current_user["id"]
        
        # Calculate date range
        now = datetime.now(timezone.utc)
        if range == "daily":
            if not from_date:
                from_date = now.date().isoformat()
            if not to_date:
                to_date = from_date
        elif range == "weekly":
            if not from_date:
                from_date = (now - timedelta(days=7)).date().isoformat()
            if not to_date:
                to_date = now.date().isoformat()
        elif range == "monthly":
            if not from_date:
                from_date = (now - timedelta(days=30)).date().isoformat()
            if not to_date:
                to_date = now.date().isoformat()
        
        # Parse dates
        from_dt = datetime.fromisoformat(from_date).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        to_dt = datetime.fromisoformat(to_date).replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
        
        # Fetch earnings data
        earnings = await db.earnings.find({
            "courier_id": courier_id,
            "created_at": {"$gte": from_dt, "$lte": to_dt}
        }).to_list(length=None)
        
        # Enrich with business names
        for earning in earnings:
            business_id = earning.get('business_id')
            if business_id:
                business = await db.businesses.find_one({"_id": business_id})
                earning['business_name'] = business.get('name', 'Bilinmiyor') if business else 'Bilinmiyor'
            else:
                earning['business_name'] = 'Bilinmiyor'
        
        # Get courier data
        courier_data = {
            'name': current_user.get('first_name', ''),
            'surname': current_user.get('last_name', ''),
            'email': current_user.get('email', ''),
            'phone': current_user.get('phone', '')
        }
        
        # Generate PDF
        pdf_buffer = create_earnings_pdf(
            courier_data=courier_data,
            earnings_data=earnings,
            date_range=range,
            from_date=from_date,
            to_date=to_date
        )
        
        filename = f"kazanc_raporu_{courier_id}_{from_date}_{to_date}.pdf"
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"PDF oluşturma hatası: {str(e)}"
        )

@router.put("/profile")
async def update_courier_profile(
    profile: ProfileUpdateRequest,
    current_user: dict = Depends(get_courier_user)
):
    """Update courier profile information"""
    try:
        from server import db
        
        courier_id = current_user["id"]
        
        # Build update dict (only include non-None values)
        update_data = {}
        if profile.name is not None:
            update_data['first_name'] = profile.name
        if profile.surname is not None:
            update_data['last_name'] = profile.surname
        if profile.phone is not None:
            update_data['phone'] = profile.phone
        if profile.email is not None:
            update_data['email'] = profile.email
        if profile.iban is not None:
            update_data['iban'] = profile.iban
        if profile.vehicleType is not None:
            update_data['vehicle_type'] = profile.vehicleType
        if profile.plate is not None:
            update_data['license_plate'] = profile.plate
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        # Update in database
        result = await db.users.update_one(
            {"id": courier_id, "role": "courier"},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Courier not found")
        
        # Fetch updated profile
        updated_courier = await db.users.find_one({"id": courier_id})
        
        return {
            "success": True,
            "message": "Profil başarıyla güncellendi",
            "profile": {
                "id": courier_id,
                "name": updated_courier.get('first_name', ''),
                "surname": updated_courier.get('last_name', ''),
                "phone": updated_courier.get('phone', ''),
                "email": updated_courier.get('email', ''),
                "iban": updated_courier.get('iban', ''),
                "vehicleType": updated_courier.get('vehicle_type', ''),
                "plate": updated_courier.get('license_plate', '')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating profile: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Profil güncelleme hatası: {str(e)}"
        )

@router.get("/availability")
async def get_courier_availability(
    current_user: dict = Depends(get_courier_user)
):
    """Get courier availability schedule"""
    try:
        from server import db
        
        courier_id = current_user["id"]
        
        courier = await db.users.find_one({"_id": courier_id, "role": "courier"})
        if not courier:
            raise HTTPException(status_code=404, detail="Courier not found")
        
        availability = courier.get('availability', [])
        
        return {
            "success": True,
            "availability": availability
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching availability: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Müsaitlik bilgisi alınamadı: {str(e)}"
        )

@router.post("/availability")
async def set_courier_availability(
    availability: AvailabilityRequest,
    current_user: dict = Depends(get_courier_user)
):
    """Set courier availability schedule (persistent)"""
    try:
        from server import db
        
        courier_id = current_user["id"]
        
        # Convert to dict for MongoDB storage
        slots_data = [slot.dict() for slot in availability.slots]
        
        # Update in database
        result = await db.users.update_one(
            {"_id": courier_id, "role": "courier"},
            {
                "$set": {
                    "availability": slots_data,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Courier not found")
        
        return {
            "success": True,
            "message": "Müsaitlik durumu kaydedildi",
            "availability": slots_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error setting availability: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Müsaitlik kaydedilemedi: {str(e)}"
        )

@router.get("/orders/history")
async def get_courier_order_history(
    status: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    business: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("createdAt:desc"),
    current_user: dict = Depends(get_courier_user)
):
    """
    Get courier order history with advanced filters
    
    Filters:
    - status: Order status (picked_up, delivered, etc.)
    - from_date, to_date: Date range (YYYY-MM-DD)
    - business: Business name (partial match)
    - city: City name
    - page, size: Pagination
    - sort: Sort field and direction (createdAt:desc, total_amount:asc, etc.)
    """
    try:
        from server import db
        
        courier_id = current_user["id"]
        
        # Build query
        query = {"courier_id": courier_id}
        
        # Status filter
        if status:
            query["status"] = status
        
        # Date range filter
        if from_date or to_date:
            date_filter = {}
            if from_date:
                from_dt = datetime.fromisoformat(from_date).replace(hour=0, minute=0, second=0, tzinfo=timezone.utc)
                date_filter["$gte"] = from_dt
            if to_date:
                to_dt = datetime.fromisoformat(to_date).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                date_filter["$lte"] = to_dt
            query["created_at"] = date_filter
        
        # City filter
        if city:
            query["city"] = {"$regex": city, "$options": "i"}
        
        # Parse sort parameter
        sort_field, sort_direction = "created_at", -1
        if ":" in sort:
            field, direction = sort.split(":")
            sort_field = field
            sort_direction = -1 if direction.lower() == "desc" else 1
        
        # Count total matching orders
        total = await db.orders.count_documents(query)
        
        # Fetch orders with pagination
        skip = (page - 1) * size
        orders = await db.orders.find(query).sort(sort_field, sort_direction).skip(skip).limit(size).to_list(length=None)
        
        # Enrich with business info and apply business filter if needed
        enriched_orders = []
        for order in orders:
            business_id = order.get('business_id')
            business_name = 'Bilinmiyor'
            business_address = ''
            
            if business_id:
                business_doc = await db.businesses.find_one({"_id": business_id})
                if business_doc:
                    business_name = business_doc.get('name', 'Bilinmiyor')
                    business_address = business_doc.get('address', '')
            
            # Apply business name filter
            if business and business.lower() not in business_name.lower():
                continue
            
            enriched_orders.append({
                "id": str(order["_id"]),
                "business_name": business_name,
                "business_address": business_address,
                "items": order.get('items', []),
                "total_amount": order.get('total_amount', 0),
                "courier_earning": order.get('totals', {}).get('courier_earning', 0),
                "status": order.get('status', ''),
                "delivery_address": order.get('delivery_address', {}),
                "city": order.get('city', ''),
                "created_at": order.get('created_at'),
                "delivered_at": order.get('delivered_at'),
                "picked_up_at": order.get('picked_up_at')
            })
        
        # Recalculate total if business filter was applied
        if business:
            total = len(enriched_orders)
        
        return {
            "success": True,
            "orders": enriched_orders,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "pages": (total + size - 1) // size
            },
            "filters": {
                "status": status,
                "from_date": from_date,
                "to_date": to_date,
                "business": business,
                "city": city,
                "sort": sort
            }
        }
        
    except Exception as e:
        print(f"❌ Error fetching order history: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Sipariş geçmişi alınamadı: {str(e)}"
        )
