package workbench.container.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.container.l01.app.Basket;
import workbench.container.l01.app.BookingClient;
import workbench.container.l01.app.BookingConfig;
import workbench.container.l01.app.BoxOffice;
import workbench.container.l01.app.InitLog;
import workbench.container.l01.app.NotAComponent;
import workbench.container.l01.app.PriceList;
import workbench.container.l01.app.RemoteBookingClient;
import workbench.container.l01.app.SalesBook;
import workbench.container.l01.app.ScanProbe;
import workbench.container.l01.app.SeatingPlan;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class WiringTest {
    private static final List<Class<?>> APP = List.of(BoxOffice.class, Basket.class, SalesBook.class,
            PriceList.class, SeatingPlan.class, RemoteBookingClient.class, BookingConfig.class);

    // --- fixtures with cycles and slow constructors, listed explicitly instead of scanned -----------

    public static class Rota { public Rota(CastList c) {} }
    public static class CastList { public CastList(RehearsalPlan p) {} }
    public static class RehearsalPlan { public RehearsalPlan(Rota r) {} }
    public static class Noticeboard { public Noticeboard(Rota r) {} }
    public static class Selfish { public Selfish(Selfish s) {} }

    public static class TwoDoors {
        public TwoDoors() {}
        public TwoDoors(SeatingPlan plan) {}
    }

    public static class Marked {
        public Marked() {}
        @Inject public Marked(SeatingPlan plan) {}
    }

    public static class SlowPlan {
        static final AtomicInteger CREATED = new AtomicInteger();
        public SlowPlan() throws InterruptedException {
            CREATED.incrementAndGet();
            Thread.sleep(50);                       // a slow start, so racing threads overlap inside it
        }
    }

    public static class SeatFinder {
        static final AtomicInteger CREATED = new AtomicInteger();
        final SlowPlan plan;
        public SeatFinder(SlowPlan plan) {
            CREATED.incrementAndGet();
            this.plan = plan;
        }
    }

    public static class Exploding {
        public Exploding() { throw new IllegalStateException("booking service key missing"); }
    }

    // --- constructors --------------------------------------------------------------------------

    @Test
    @DisplayName("pick returns the only public constructor")
    void picksTheOnlyConstructor() throws Exception {
        assertThat(Constructors.pick(PriceList.class)).isEqualTo(PriceList.class.getConstructor(SeatingPlan.class));
    }

    @Test
    @DisplayName("pick prefers the @Inject constructor, and refuses to guess between two unmarked ones")
    void injectWinsAndTwoIsAmbiguous() throws Exception {
        assertThat(Constructors.pick(Marked.class)).isEqualTo(Marked.class.getConstructor(SeatingPlan.class));
        assertThatThrownBy(() -> Constructors.pick(TwoDoors.class))
                .isInstanceOf(ContainerException.class)
                .hasMessage("TwoDoors has 2 public constructors; mark the one to use with @Inject");
    }

    @Test
    @DisplayName("pick ignores Kotlin's synthetic constructor for default arguments")
    void kotlinSyntheticConstructor() throws Exception {
        assertThat(KotlinPrices.class.getConstructors()).hasSize(2);
        assertThat(Constructors.pick(KotlinPrices.class)).isEqualTo(KotlinPrices.class.getConstructor(SeatingPlan.class, int.class));
    }

    @Test
    @DisplayName("a Kotlin class whose parameters all have defaults has two real constructors, even with @Inject")
    void kotlinAllDefaults() {
        assertThatThrownBy(() -> Constructors.pick(DefaultedPrices.class))
                .isInstanceOf(ContainerException.class)
                .hasMessage("DefaultedPrices has 2 public constructors; mark the one to use with @Inject");
        assertThatThrownBy(() -> Constructors.pick(InjectedPrices.class))
                .isInstanceOf(ContainerException.class)
                .hasMessage("InjectedPrices has 2 @Inject constructors; keep one");
    }

    // --- the graph -------------------------------------------------------------------------------

    @Test
    @DisplayName("creation order lists every component once, each after all of its dependencies")
    void dependenciesComeFirst() {
        BeanGraph graph = new BeanGraph(APP);
        List<Class<?>> order = graph.creationOrder();
        assertThat(order).containsExactlyInAnyOrderElementsOf(APP);
        for (Class<?> c : order) {
            for (Class<?> dep : graph.dependenciesOf(c)) {
                assertThat(order.indexOf(dep)).as(dep.getSimpleName() + " before " + c.getSimpleName())
                        .isLessThan(order.indexOf(c));
            }
        }
    }

    @Test
    @DisplayName("a cycle is reported with its path, from the repeated class back to itself")
    void cycleMessage() {
        assertThatThrownBy(() -> new BeanGraph(List.of(Rota.class, CastList.class, RehearsalPlan.class)).creationOrder())
                .isInstanceOf(ContainerException.class)
                .hasMessage("Dependency cycle: Rota -> CastList -> RehearsalPlan -> Rota");
        assertThatThrownBy(() -> new BeanGraph(List.of(Noticeboard.class, Rota.class, CastList.class, RehearsalPlan.class)).creationOrder())
                .as("the path starts at the cycle, not at Noticeboard")
                .hasMessage("Dependency cycle: Rota -> CastList -> RehearsalPlan -> Rota");
        assertThatThrownBy(() -> new BeanGraph(List.of(Selfish.class)).creationOrder())
                .hasMessage("Dependency cycle: Selfish -> Selfish");
    }

    @Test
    @DisplayName("the container checks the whole graph when it is built, before anyone asks for a bean")
    void failsFast() {
        assertThatThrownBy(() -> new Container(List.of(Noticeboard.class, Rota.class, CastList.class, RehearsalPlan.class)))
                .isInstanceOf(ContainerException.class)
                .hasMessageContaining("Dependency cycle");
        assertThatThrownBy(() -> new Container(List.of(BoxOffice.class, SalesBook.class)))
                .isInstanceOf(ContainerException.class)
                .hasMessage("BoxOffice needs BookingClient: No component provides BookingClient");
    }

    // --- scopes --------------------------------------------------------------------------------

    @Test
    @DisplayName("a singleton is created once and shared by everyone who needs it")
    void singletonsAreShared() {
        Container c = new Container(APP);
        BoxOffice office = c.get(BoxOffice.class);
        assertThat(c.get(BoxOffice.class)).isSameAs(office);
        assertThat(office.prices()).isSameAs(c.get(PriceList.class));
        assertThat(office.prices().plan()).isSameAs(c.get(SeatingPlan.class));
        assertThat(office.booking()).isInstanceOf(RemoteBookingClient.class).isSameAs(c.get(BookingClient.class));
        assertThat(((RemoteBookingClient) office.booking()).config()).isSameAs(c.get(BookingConfig.class));
        assertThat(office.sell("C12", 12_000)).isEqualTo("hold-C12-12000");
        assertThat(c.get(SalesBook.class).lines()).containsExactly("hold-C12-12000 fee=348");
    }

    @Test
    @DisplayName("a prototype is new on every get, while its singleton dependencies are shared")
    void prototypesAreNew() {
        Container c = new Container(APP);
        Basket first = c.get(Basket.class);
        Basket second = c.get(Basket.class);
        assertThat(first).isNotSameAs(second);
        assertThat(first.prices()).isSameAs(second.prices()).isSameAs(c.get(PriceList.class));
    }

    @Test
    @DisplayName("eight threads asking for a new singleton at once get one instance, built once")
    void oneInstanceUnderConcurrentFirstAccess() throws Exception {
        Container c = new Container(List.of(SeatFinder.class, SlowPlan.class));
        int plansBefore = SlowPlan.CREATED.get();
        int findersBefore = SeatFinder.CREATED.get();
        CountDownLatch go = new CountDownLatch(1);
        Set<Object> seen = ConcurrentHashMap.newKeySet();
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            Thread t = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                seen.add(c.get(SeatFinder.class));
            });
            t.start();
            threads.add(t);
        }
        go.countDown();
        for (Thread t : threads) t.join();
        assertThat(seen).hasSize(1);
        assertThat(SlowPlan.CREATED.get() - plansBefore).as("SlowPlan constructor calls").isEqualTo(1);
        assertThat(SeatFinder.CREATED.get() - findersBefore).as("SeatFinder constructor calls").isEqualTo(1);
    }

    @Test
    @DisplayName("a failing constructor surfaces its own exception as the cause, and a later get tries again")
    void constructorFailure() {
        Container c = new Container(List.of(Exploding.class));
        for (int attempt = 0; attempt < 2; attempt++) {
            assertThatThrownBy(() -> c.get(Exploding.class))
                    .isInstanceOf(ContainerException.class)
                    .hasMessageContaining("Exploding")
                    .cause().isInstanceOf(IllegalStateException.class).hasMessage("booking service key missing");
        }
    }

    // --- scanning (given code: these pass from the start) ---------------------------------------

    @Test
    @DisplayName("the scanner finds the @Component classes of one package without initializing them")
    void scanFindsComponents() {
        List<Class<?>> found = ClassScanner.scan(getClass().getClassLoader(), "workbench.container.l01.app");
        assertThat(found).contains(BoxOffice.class, RemoteBookingClient.class, ScanProbe.class)
                .doesNotContain(NotAComponent.class, BookingClient.class);
        assertThat(InitLog.INITIALIZED).as("static initializers that ran").doesNotContain("ScanProbe");
    }
}
