from core.models.common import BaseModel
import peewee as pw


class Rule(BaseModel):

    plugin = pw.CharField(max_length=50, null=False)

    name = pw.CharField(max_length=50,null=False)
    description = pw.TextField(null=True)
    priority = pw.IntegerField(default=0, null=False)

    # Indique si la règle peut être déclenchée
    triggerable = pw.BooleanField(default=False, null=False)

    # Durée (en s) pendant laquelle une régle ne peut pas être redéclenchée
    disable_delay = pw.IntegerField(default=0, null=False)

    trigger_count = pw.IntegerField(default=0, null=False)
    triggered_at = pw.TimestampField(null=True)

    def __str__(self):
        return f"Rule {self.name} of {self.plugin}"

    # def as_dict(self):
    #     return {
    #         "name": self.name,
    #         "description": self.description,
    #         "priority": self.priority,
    #         "db_id": self.db_id,
    #         "uid": self.uid,
    #     }
    #
    # def get_premises(self):
    #     return Premise.get_by_rule_id(self.db_id)
    #
    # def get_actions(self):
    #     return Action.get_by_rule_id(self.db_id)
    #
    # @staticmethod
    # def load_all(uid):
    #     # On récupère toutes les règles
    #     rules = Rule.get_all(uid)
    #
    #     result = []
    #
    #     # On itère pour ajouter à chacune les premisses et les actions (et le groupe)
    #     for r in rules:
    #         rdic = r.as_dict()
    #
    #         p_list = Premise.get_by_rule_id(r.db_id)
    #         a_list = Action.get_by_rule_id(r.db_id)
    #         rdic["if"] = p_list
    #         rdic["then"] = a_list
    #         result.append(rdic)
    #
    #     return result
    #
    # @staticmethod
    # def get_all(uid):
    #     pool = DatabaseService()  # Singleton
    #     conn = None
    #     res = None
    #
    #     list = []
    #
    #     try:
    #         sql = f"SELECT * from RULE WHERE uid={sanitize(uid)}"
    #
    #         conn = pool.get_connection()  # Singleton
    #         cursor = conn.cursor()
    #
    #         cursor.execute(sql)
    #
    #         for row in cursor:  # on les prends un par un...
    #             list.append(Rule(dict(row)))
    #
    #     except Exception as e:
    #         print(e)
    #         pass
    #     finally:
    #         pool.release_connection(conn)
    #
    #     # le res retourné par la requete n'est pas un "vrai" dico et il manque en partculier la méthofde get
    #     return list
    #
    # @staticmethod
    # def get_candidates(uid):
    #     pool = DatabaseService()  # Singleton
    #     conn = None
    #     res = None
    #
    #     list = []
    #
    #     try:
    #         sql = f"SELECT * from RULE WHERE uid={sanitize(uid)} and triggerable=true"
    #
    #         conn = pool.get_connection()  # Singleton
    #         cursor = conn.cursor()
    #
    #         cursor.execute(sql)
    #
    #         for row in cursor:  # on les prends un par un...
    #             list.append(Rule(dict(row)))
    #
    #     except Exception as e:
    #         print(e)
    #         pass
    #     finally:
    #         pool.release_connection(conn)
    #
    #     # le res retourné par la requete n'est pas un "vrai" dico et il manque en partculier la méthofde get
    #     return list

