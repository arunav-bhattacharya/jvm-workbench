package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

@Component
public class SeatingPlan {
    public boolean isStalls(String seat) { return seat.charAt(0) <= 'M'; }
}
