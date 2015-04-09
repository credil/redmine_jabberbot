select u.login, max(te.updated_on) 
from time_entries te, users u 
where u.id = te.user_id 
group by u.login 
order by max(te.updated_on);
