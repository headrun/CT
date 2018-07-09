import MySQLdb

class FinanceAgentCompare:
	def main(self):
		conn = MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'root', db = 'SEATFINDERDB', charset="utf8", use_unicode=True)
		cur = conn.cursor()
		cur.execute('select * from agent_called where final_status!="Pending" and amount!=""')
		rows = cur.fetchall()
		for row in rows:
			sk, agent,airline,pnr,pcc,ticket_number,status,remarks,booking_date,travelling_date,agent_amount,final_status,genyses_extension_number, created_at,action_modified_at = row
			if 'Air Asia' in airline:
				airline='Airasia'
			cur.execute('select pnr,total_refund_amount from finance_uploads where pnr="%s" and airline="%s"'%(pnr,airline))
			rows = cur.fetchall()
			#if not rows:
			#	return
			total_amount =[]
			for row in rows:
				finance_pnr,finance_total_amount_refund= row
				total_amount.append(finance_total_amount_refund)
			
			discrepancy = ''
			#finance_total_amount = sum(Decimal(i) for i in total_amount)
			finance_total_amount = sum(int(i) for i in total_amount)
			if int(finance_total_amount)>=int(agent_amount) and int(finance_total_amount)!=0 and int(agent_amount)!=0 and agent_amount!='':
				discrepancy ='Full Refund'
			elif int(finance_total_amount) < int(agent_amount) and int(finance_total_amount)!=0 and agent_amount!='':
				discrepancy = 'Partial Refund'
			
			elif int(finance_total_amount)==0 and int(agent_amount)>0:
					discrepancy='Yet to get Refund'
			else:
				discrepancy = 'no refund'
				
			insert_query = 'insert into discrepancy(sk,airline,pnr,pcc,ticket_number, agent, agent_calling_status, agent_action_date, finance_amount,agent_amount, discrepancy_status ,created_at,modified_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), pnr=%s, ticket_number=%s, agent=%s, finance_amount=%s, agent_amount = %s ,discrepancy_status=%s'
			vals = (str(sk),str(airline),str(pnr),str(pcc),str(ticket_number),str(agent),str(final_status) ,str(action_modified_at),str(finance_total_amount),str(agent_amount) , str(discrepancy), str(pnr),str(ticket_number),str(agent),str(finance_total_amount),str(agent_amount),str(discrepancy))
			try:
				cur.execute(insert_query, vals)
			except Exception as e:
				print 'some insert error'
			conn.commit()

if __name__=="__main__":
    FinanceAgentCompare().main()
