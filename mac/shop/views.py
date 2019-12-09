from django.shortcuts import render
from django.http import HttpResponse
from .models import Product, Contact, Orders, OrderUpdate
from math import ceil
from django.views.decorators.csrf import csrf_exempt
from PayTm import Checksum
import json
# Create your views here.
MERCHANT_KEY = '**********'

def searchMatch(query, item):
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False

def search(request):
    query = request.GET.get('search')
    products = Product.objects.all()
    print(products)
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]
        n = len(prod)
        nSlide = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) !=0:
            allProds.append([prod, range(1, nSlide), nSlide])
    params = {'allProds': allProds}
    return render(request, 'shop/index.html', params)
def index(request):
    products = Product.objects.all()
    print(products)
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlide = n//4 + ceil((n/4)-(n//4))
        allProds.append([prod, range(1, nSlide), nSlide])
    params = {'allProds': allProds}
    return render(request, 'shop/index.html', params)
def about(request):
    return render(request, 'shop/about.html')

def contact(request):
    thank=False
    if request.method == 'POST':
        name =request.POST.get('name','')
        email =request.POST.get('email','')
        number =request.POST.get('number','')
        desc =request.POST.get('desc','')
        contact = Contact(name=name, email=email, number=number, desc=desc)
        contact.save()
        thank = True
    return render(request, 'shop/contact.html', {'thank':thank})

def prodView(request, myid):
    #Fetch the product using id
    product = Product.objects.filter(id=myid)
    print(product)
    return render(request, 'shop/prodView.html', {'product':product[0]})




def checkout(request):
    if request.method == 'POST':
        items_json = request.POST.get('itemsJson','')
        name =request.POST.get('name','')
        amount = request.POST.get('amount','')
        email =request.POST.get('email','')
        number =request.POST.get('number','')
        address = request.POST.get('address1','') +" "+ request.POST.get('address2','')
        city =request.POST.get('city','')
        state =request.POST.get('state','')
        zip_code =request.POST.get('zip_code','')
        order = Orders(items_json=items_json,amount=amount, name=name, email=email, number=number, address=address, city=city, state=state, zip_code=zip_code)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The Order Has been Placed.")
        update.save()
        thank = True
        id = order.order_id
        # return render(request, 'shop/checkout.html', {'thank': thank,'id':id })
        # Request Paytm to transfer amount
        param_dict = {
            'MID': 'wSDErO91051360606417',
            'ORDER_ID': str(order.order_id),
            'TXN_AMOUNT': str(amount),
            'CUST_ID': email,
            'INDUSTRY_TYPE_ID': 'Retail',
            'WEBSITE': 'WEBSTAGING',
            'CHANNEL_ID': 'WEB',
            'CALLBACK_URL':'http://127.0.0.1:8000/shop/handlerequest/',
        }
        param_dict['CHECKSUMHASH']= Checksum.generate_checksum(param_dict,MERCHANT_KEY)
        return render(request, 'shop/paytm.html',{'param_dict':param_dict})
    return render(request, 'shop/checkout.html')


def tracker(request):
    if request.method == 'POST':
        order_id =request.POST.get('OrderId','')
        email =request.POST.get('email','')
        try:
            order = Orders.objects.filter(order_id=order_id, email = email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id=order_id)
                updates = []
                for item in update:
                    updates.append({'text':item.update_desc, 'time':item.timestamp})
                    response = json.dumps([updates,order[0].items_json], default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{}')
        except Exception as e:
            return HttpResponse('{}')
    return render(request, 'shop/tracker.html')

@csrf_exempt
def handlerequest(request):
    form = request.POST;
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]
    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print('order successful')
        else:
            print('order was not successful' + response_dict['RESPMSG'])
    return render(request, 'shop/paymentstatus.html', {'response': response_dict})
