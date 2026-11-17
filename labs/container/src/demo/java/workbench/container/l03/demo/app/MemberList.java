package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

@Component
public class MemberList {
    public boolean isMember(String customerId) { return customerId.startsWith("m-"); }
}
