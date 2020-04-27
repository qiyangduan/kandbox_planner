import datetime
import pandas as pd
import numpy as np 
import json
import glob
import math
import xmlrpc.client
from datetime import datetime, timedelta 

import kandbox_planner.config as config
import kandbox_planner.util.planner_date_util  as date_util

# CURRENT_DATE = '01/09/19'
KANDBOX_DATE_FORMAT= "%Y%m%d"
SYSTEM_DATE_FORMAT = "%Y-%m-%d" 
# datetime.strptime('2019-07-01',"%Y-%m-%d")
ORIG_SYS_DATE_FORMAT = '%m/%d/%Y'




class KPlanner2OdooAPIAdapter:
    working_dir = None
    def __init__(self, working_dir = '/tmp',connect_dict=None ):      
        self.working_dir = working_dir
        self.connect_dict = connect_dict
        self.connect() 
 
    def connect(self):
        self.url = config.odoo_url # 'http://localhost:8069'
        # db =  'local_demo_1'
        # db = 'docker_riusa_history_db'
        self.db = config.odoo_db # 'r  iusa_1'
        #self.username = 'admin'
        #self.password = 'admin'
        self.username = config.odoo_username # 
        self.password = config.odoo_password# 

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.url))
        # print(common.version())
  
        self.uid = common.authenticate(self.db, self.username, self.password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.url))
        return self.models

    #models = connect_to_odoo()

    def get_worker_id_dict (self):
        odoo_worker_dict = {}

        p = self.models.execute_kw(self.db, self.uid, self.password,
            'fsm.person', 'search_read',
            [[['name', 'like', '401%'] ]],
            {'fields': ['name', 'id', 'company_id']}   )
        # p
        for ap in p:
            odoo_worker_dict[ap['name']] = ap['id']
        self.worker_id_dict = odoo_worker_dict
        return odoo_worker_dict
        #for ap in p:
        #    models.execute_kw(self.db, self.uid, self.password,  'fsm.person', 'unlink', [ap['id']]) # fsm.person

    def get_order_type_id_dict (self): 
        odoo_dict = {}
        p = self.models.execute_kw(self.db, self.uid, self.password,
            'fsm.order.type', 'search_read',
            [[ ]],
            )   # {'limit': 2}  
        # p
        #for ap in p:
        #    models.execute_kw(db, uid, password,  'fsm.person', 'unlink', [ap['id']]) # fsm.person

        for ap in p:
            odoo_dict[ap['name']] = ap['id']
        odoo_dict.keys()
        self.order_type_id_dict = odoo_dict
        return odoo_dict

    def reset_all_orders(self):
        '''

            update  fsm_order set stage_id = 1,  person_id = cast (description as integer), scheduled_date_start = request_early ;
            commit;

        '''
        p = self.models.execute_kw(self.db, self.uid, self.password,
            'fsm.order', 'search_read',
            [[ ]], #    ['name', '=', '10740330|1409|01-05-00002|44334150|050745861-000' ]
            {'limit': 2000}   ) # 'fields': ['name', 'id', 'date'], 
        #p
        print("To Reset nbr of rows " , len(p))
        for ap in p:
            print("Reset original order: {} start time : {} to {}, from stage {}"\
                .format( ap['name'], ap['scheduled_date_start'], ap['request_early'], ap['stage_id']) )
            #new_date_str = datetime.strftime(datetime.strptime(str( order['scheduled_start_day']),  KANDBOX_DATE_FORMAT) \
            #    + timedelta(minutes = order['scheduled_start_minutes'] + (6*60))        , '%Y-%m-%d %H:%M:%S')

            id = self.models.execute_kw(self.db, self.uid, self.password, 'fsm.order', 'write', [ [p[0]['id']],  { 
                            # 'name': row['visit_id_'],    
                            'person_id': ap['description'],   
                            'stage_id':1, # Inplanning
                            'scheduled_date_start': ap['request_early'],  #        scheduled_date_start, 
                        }])
        
    def get_location_id_dict (self): 
        odoo_cust_dict = {}
        p = self.models.execute_kw(self.db, self.uid, self.password,
            'fsm.location', 'search_read',
            [[ ['id', '!=', 1] ]],
            {'fields': ['ref', 'id' ]}  ) # 'limit': 10000,
        for ap in p:
            odoo_cust_dict[ap['ref']] = ap['id']
        odoo_cust_dict.keys()
        self.location_id_dict = odoo_cust_dict
        return odoo_cust_dict
        '''

        for ap in p:
            print('deleting: ',ap['id'] )
            self.models.execute_kw(self.db, self.uid, self.password,  'fsm.location', 'unlink', [ap['id']]) # fsm.person
        '''

    def kandbox_orders_to_odoo(self, order=None):
        # o = [{'job_index': 2, 'job_id': 23, 'scheduled_day_index': 0, 'scheduled_start_minutes': 450.0, 'scheduled_duration_minutes': 90, 'scheduled_worker_index': 3, 'scheduled_worker_id': 4, 'planning_status': 'I', 'requested_start_day': 12, 'scheduled_start_day': '20191202', 'job_code': '10678936|62|01-05-00002|54289009|054294261-000', 'scheduled_worker_code': '401-503'}, ]
        
        # order = o[0]
        # for order in new_orders:
        p = self.models.execute_kw(self.db, self.uid, self.password,
            'fsm.order', 'search_read',
            [[ ['name', '=', order['job_code']] ]],
            { 'limit': 1,}  )
        # 10678936|50|01-05-00002|47686502|050500841-000
        if len(p) < 1:
            print("Kplanner can not find job: {} ".format( order['job_code'] )  ) 
            return 'NotFound'
        ap = p[0]
        new_date_str = datetime.strftime(datetime.strptime(str( order['scheduled_start_day']),  KANDBOX_DATE_FORMAT) \
            + timedelta(minutes = order['scheduled_start_minutes'] )        , '%Y-%m-%d %H:%M:%S')   # + (6*60) no timezone shift
        print("Kplanner will change order {} start: {}, to start: {} and stage 2".format( ap['name'], ap['scheduled_date_start'],  new_date_str )  ) 

        id = self.models.execute_kw(self.db, self.uid, self.password, 'fsm.order', 'write', [ [p[0]['id']],  { 
                        # 'name': row['visit_id_'],    
                        'person_id': self.worker_id_dict[order['scheduled_worker_code']],   
                        'stage_id':2, # Inplanning
                        'scheduled_date_start': new_date_str,  #        scheduled_date_start,
                        # 'scheduled_duration':  order['scheduled_duration_minutes'] / 60, 
                    }])
        return 'OK'
    def odoo_orders_to_kandbox(self):

        p = self.models.execute_kw(self.db, self.uid, self.password,
            'fsm.order', 'search_read',
            [[ ['id', '!=', 1] ]],
            { 'limit': 1,}  )
        print(p)


    def insert_all_orders(self):
        odoo_cust_dict = self.worker_id_dict

        service_cover = pd.read_csv('{}/nov_dec_data/05_SPPL_US_D_ServiceCover_D_401_012_000366970_20191021_2046.csv'.format(working_dir), 
                        header = 0,
                        delimiter=';' )

        service_cover['service_cover_id_'] = service_cover.apply(lambda x:  '|'.join( [ str(x['ContractNumber']) 
                                                                    ,str(x['PremiseNumber'])
                                                                    ,x['ProductCode'] ,  
                                                                    str(x['ServiceCoverNumber'])]) , axis=1 )
        visit = pd.read_csv('{}/nov_dec_data/05_SPPL_US_D_Visit_D_401_012_000366970_20191021_2046_PN.csv'.format(working_dir), 
                        header = 0,
                        delimiter=';' )

        visit['visit_id_'] = visit.apply(lambda x: '|'.join( [ 
                                                    str(x['ContractNumber']),  
                                                    str(x['PremiseNumber']),   
                                                        x['ProductCode'],  
                                                        str(x['ServiceCoverNumber']),   
                                                        str(x['Visit No']) ]), axis=1)
        visit['service_cover_id_'] = visit.apply(lambda x:  '|'.join( [ str(x['ContractNumber']) 
                                                                    ,str(x['PremiseNumber'])
                                                                    ,x['ProductCode'] ,  
                                                                    str(x['ServiceCoverNumber'])]) , axis=1 )
        visit['location_id_'] = visit.apply(lambda x:  '|'.join( [ str(x['ContractNumber']) 
                                                                    ,str(x['PremiseNumber']) ]) , axis=1 )
        visit_with_sc = pd.merge(visit, 
                                    service_cover[ ['service_cover_id_', 'ActualPlanTime', 'STT', 'AvTreatTime',
                                                'LastVisitDate', 'Appointment','ServiceArea', 'Employee', 'SpecialInstruction'] ],
                                    how='inner', 
                    left_on=   [ 'service_cover_id_' ], 
                    right_on = [ 'service_cover_id_' ]).sort_values( [ 'ContractNumber' ])
        visit_with_sc.count().max()
        visit_with_sc['Visit_Start_Time'].fillna(0,inplace=True)
        visit_with_sc['ServiceTimeStart_minutes'] = visit_with_sc.apply(lambda x:  60* math.floor( x['Visit_Start_Time']/100) +  ( x['Visit_Start_Time'] % 100 ) \
                                                                       , axis=1 )
        #visit['ServiceTimeEnd_minutes'] = visit.apply(lambda x:  get_right_end_minutes ( x['ServiceTimeStart_minutes'], time_string_hhmm_to_minutes(x['ServiceTimeEnd']) ) , axis=1 )

        visit_with_sc['ActualPlanTime'].fillna(0,inplace=True)

        visit_with_sc['visit_duration_minutes'] =visit_with_sc.apply(lambda x:   date_util.time_string_hhmm_to_minutes(x['ActualPlanTime']  )  , axis=1 )
        visit_with_sc['PlannedVisitDate'] = visit_with_sc['Date'] 

        visit_with_sc['PlannedVisitDate_date'] =visit_with_sc.apply(lambda x:   datetime.strptime(x['Date'], ORIG_SYS_DATE_FORMAT ) , axis=1)

        visit_with_sc['line_of_business_code'] =visit_with_sc.apply(lambda x:  int(x['ProductCode'].split('-' )[0] ), axis=1)
        print(visit_with_sc.count().max())

        # visit['Visit_Status'] = visit.apply(lambda x:  decode_visit_status( x) , axis=1 )
        visit_with_sc = visit_with_sc[  ( visit_with_sc['PlannedVisitDate_date'] >=  datetime.strptime('20191202', KANDBOX_DATE_FORMAT ) ) & \
             (  visit_with_sc['PlannedVisitDate_date'] <=  datetime.strptime('20191209', KANDBOX_DATE_FORMAT )  )]
        print(visit_with_sc.count().max())


        print("nbr of visits all: ",visit_with_sc.count().max())
        # test_mode = False
        for index, row in visit_with_sc.iterrows():
            #print(row['service_area_code'], row['LineOfBusiness'])
            # print(row['visit_duration_minutes'])
            
            loc_ref = '|'.join( [ str(row['ContractNumber'])  ,str(row['PremiseNumber']) ])
            # print( loc_ref , self.location_id_dict[loc_ref])
            
            # print( row['PlannedVisitDate_date'] + timedelta( minutes=int(row['ServiceTimeStart_minutes']) ) )

            if row['VisitOwner_Default'] not in self.worker_id_dict.keys():
                # odoo_worker_dict[order['VisitOwner_Default']] = index
                print(index, ": ", row['VisitOwner_Default'], " as default owner is skipped.")
                continue

            scheduled_date_start = row['PlannedVisitDate_date'] + timedelta( minutes=int(row['ServiceTimeStart_minutes']) )
            id = self.models.execute_kw(self.db, self.uid, self.password, 'fsm.order', 'create', [{ 
                'name': row['visit_id_'],    # "{} {}".format(row['Forename'], row['Surname']), 
                'person_id': self.worker_id_dict[row['VisitOwner_Default']], 
                'team_id': 1,
                'location_id':self.location_id_dict[loc_ref],
                'type':self.order_type_id_dict[str(int(row['ProductCode'].split('-')[0]))],
                'company_id':1,
                'description': 'riusa' ,  
                'scheduled_date_start': datetime.strftime(scheduled_date_start, '%Y-%m-%d %H:%M:%S'), 
                'scheduled_duration':row['visit_duration_minutes']/60, 

            }])


if __name__ == '__main__': 

    # exit(0)
    odoo = KPlanner2OdooAPIAdapter(working_dir = '/x/pilot_20191030_2nd_start/working_area_20191201')

    # odoo.delete_all_locations()
    # id_dict = odoo.insert_all_locations()

    # odoo.delete_all_orders()
    # odoo.insert_all_orders()
    # odoo.odoo_orders_to_kandbox()
    b = odoo.get_worker_id_dict() 
    # odoo.kandbox_orders_to_odoo()
    odoo.reset_all_orders()

    #exit(0) 
    
    # print(id_dict)
    #a = odoo.get_location_id_dict()
    #c = odoo.get_order_type_id_dict()

