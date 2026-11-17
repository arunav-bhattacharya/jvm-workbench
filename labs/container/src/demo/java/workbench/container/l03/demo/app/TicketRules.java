package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

@Component
public class TicketRules {
    private final MemberList members;

    public TicketRules(MemberList members) { this.members = members; }

    public boolean allow(String customerId, long priceCents) {
        return members.isMember(customerId) || priceCents < 50_000;   // only members may buy the boxes
    }
}
