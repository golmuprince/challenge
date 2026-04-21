
from my_agents.Menu_agent import menu_agent
from my_agents.Order_agent import order_agent
from my_agents.Reservation_agent import reservation_agent

menu_agent.handoffs = [order_agent, reservation_agent]
order_agent.handoffs = [menu_agent, reservation_agent]
reservation_agent.handoffs = [menu_agent, order_agent]