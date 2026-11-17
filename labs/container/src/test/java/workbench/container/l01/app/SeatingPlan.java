package workbench.container.l01.app;

import workbench.container.l01.Component;

@Component
public class SeatingPlan {
    public boolean isStalls(String seat) {
        return seat.charAt(0) <= 'M';
    }
}
