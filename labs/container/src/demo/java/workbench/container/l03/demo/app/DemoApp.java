package workbench.container.l03.demo.app;

import workbench.container.l03.Registry;
import workbench.container.l03.ShowArchive;
import workbench.container.l03.ShowCloser;

import java.util.List;

/** The capstone's box office app: 14 components, two of them intercepted (one by interface, one by subclass). */
public final class DemoApp {
    private DemoApp() {}

    public static final List<Class<?>> COMPONENTS = List.of(
            BoxOffice.class, ReturnsDesk.class, ClosingJob.class, Basket.class,
            RemoteBookingClient.class, BookingConfig.class,
            PriceList.class, SeatingPlan.class, TicketRules.class, MemberList.class, SalesBook.class,
            ShowCloser.class, ShowArchive.class, ShowClock.class);

    /** One sale, one return, one closing: every component and both kinds of interception get used. */
    public static String run(Registry registry) {
        String hold = registry.get(BoxOffice.class).sell("m-42", "C12", 12_000);
        String back = registry.get(ReturnsDesk.class).takeBack(hold);
        String closed = registry.get(ClosingJob.class).run("N-17");
        long fee = registry.get(Basket.class).feeCents(12_000);
        return hold + ", " + back + ", " + closed + ", fee " + fee + ", sales book lines " + registry.get(SalesBook.class).size();
    }
}
