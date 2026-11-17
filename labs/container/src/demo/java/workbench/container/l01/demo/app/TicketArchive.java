package workbench.container.l01.demo.app;

import workbench.container.l01.Component;

@Component
public class TicketArchive {
    static {
        System.out.println("  TicketArchive.<clinit>: loading 40,000 old tickets");   // runs on first active use only
    }
}
