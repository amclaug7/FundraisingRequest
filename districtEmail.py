import os
import json
import requests
import csv
import smtplib
import getpass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import plotly as py
from plotly.graph_objs import *


username = input("Enter your username: ")
pw = getpass.getpass("Enter your password: ")
fro = input("From: ")+"@dtcc.edu"

district = []
count = []


def readAddresses():
    readFile = open('StudentInfo.csv', 'r')
    readFileReader = csv.reader(readFile)

    next(readFileReader)

    for row in readFileReader:
        studentName = row[0]
        mail = row[1]
        address = row[2]
        repName = getRepName(address)
        sendEmail(mail, studentName, repName)
        graphCount()

    readFile.close()


def getRepName(address):
    geocodeURL = 'http://www.mapquestapi.com/geocoding/v1/address?key=koBSx5A8tI3GQVXABdi6F7vGNdhwiESn&location=' + \
                 address + '.De'
    res = requests.get(geocodeURL)

    writeCoordinates = open('coor.json', 'wb')

    for chunk in res.iter_content(100000):
        writeCoordinates.write(chunk)

    writeCoordinates.close()

    coor = open('coor.json', 'r')
    data = coor.read()
    coorData = json.loads(data)

    lat = str(coorData['results'][0]['locations'][0]['latLng']['lat'])
    long = str(coorData['results'][0]['locations'][0]['latLng']['lng'])

    coor.close()

    repInfoURL = 'http://openstates.org/api/v1/legislators/geo/?lat=' + lat + '&long=' + long + \
                 '&apikey=fc3537cb-b732-4d67-8c94-e453da27a45a'

    res = requests.get(repInfoURL)

    writeData = open('repinfo.json', 'wb')

    for chunk in res.iter_content(100000):
        writeData.write(chunk)

    writeData.close()

    rep = open('repinfo.json', 'r')
    data = rep.read()
    repData = json.loads(data)

    rep.close()

    return str(repData[0]['full_name'])


def sendEmail(emailaddress, studentName, repName):
    coor = open('coor.json', 'r')
    data = coor.read()
    coorData = json.loads(data)

    lat = str(coorData['results'][0]['locations'][0]['latLng']['lat'])
    long = str(coorData['results'][0]['locations'][0]['latLng']['lng'])

    coor.close()

    mapURL = 'https://open.mapquestapi.com/staticmap/v5/map?key=koBSx5A8tI3GQVXABdi6F7vGNdhwiESn' + \
             '&boundingBox=39.60,-76.00,38.75,-75.00&size=600,800@2x&locations=' + lat + ',' + long

    rep = open('repinfo.json', 'r')
    data = rep.read()
    repData = json.loads(data)

    repEmail = repData[0]['email']
    repPhone = repData[0]['offices'][0]['phone']

    rep.close()

    smtpObj = smtplib.SMTP('smtp.dtcc.edu', 587)
    smtpObj.ehlo()
    smtpObj.starttls()

    smtpObj.login(username + "@dtcc.edu", pw)

    msg = MIMEMultipart()
    msg["From"] = fro
    msg["To"] = emailaddress
    msg["Subject"] = "Contact Your State Rep About Prop 611"
    htmlbody = """\
    <html>
    	<body>
    	    <p>""" + studentName + """,
    	    <br>
    		<p>This is a reminder to contact your state representative about Prop 611 by emailing """ + repName + """ at """ + \
                repEmail + """ or call their office at """ + repPhone + """.</p>
                <br>
            <a href=""" + mapURL + """>Confirm Location</a>
    	</body>
    </html>
    """

    body = MIMEText(htmlbody, 'html')
    msg.attach(body)

    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(open('SampleLetter.txt', 'rb').read())
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename('SampleLetter.txt'))

    msg.attach(attachment)

    smtpObj.sendmail(msg["From"], msg["To"], msg.as_string())
    smtpObj.quit()


def graphCount():
    rep = open('repinfo.json', 'r')
    data = rep.read()
    repData = json.loads(data)

    rep.close()

    districtNo = repData[0]['district']

    if districtNo in district:
        index = district.index(districtNo)
        tally = count[index] + 1
        del count[index]
        count.insert(index, tally)
    else:
        district.append(districtNo)
        count.append(1)


def grapher():
    districtData = Bar(
        x=district,
        y=count
    )

    data = [districtData]

    layout = Layout(
        title='Student Congressional Density',
        xaxis=dict(
            title='Congressional District',
        ),
        yaxis=dict(
            title='No. of Students',
        )
    )

    fig = Figure(data=data, layout=layout)
    py.offline.plot(fig, filename='graph.html')


def main():
    readAddresses()
    grapher()
    os.remove('coor.json')
    os.remove('repinfo.json')


main()