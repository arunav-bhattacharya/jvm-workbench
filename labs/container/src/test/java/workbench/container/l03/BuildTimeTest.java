package workbench.container.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import workbench.container.l03.app.Basket;
import workbench.container.l03.app.BookingClient;
import workbench.container.l03.app.BookingConfig;
import workbench.container.l03.app.BookingScript;
import workbench.container.l03.app.BoxOffice;
import workbench.container.l03.app.PriceList;
import workbench.container.l03.app.RemoteBookingClient;
import workbench.container.l03.app.SalesBook;
import workbench.container.l03.app.SeatFinder;
import workbench.container.l03.app.SeatingPlan;
import workbench.container.l03.app.SlowPlan;

import java.lang.reflect.Proxy;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CountDownLatch;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class BuildTimeTest {
    private static final String NAME = "workbench.container.l03.gen.AppRegistry";
    private static final List<Class<?>> APP = List.of(BoxOffice.class, Basket.class, SalesBook.class,
            PriceList.class, SeatingPlan.class, RemoteBookingClient.class, BookingConfig.class, BookingScript.class,
            ShowCloser.class, ShowArchive.class, SeatFinder.class, SlowPlan.class);

    @TempDir
    static Path build;
    private static String source;
    private static Path classes;

    // the "build": generate and compile once, on first use; every test then loads a fresh copy of the class
    private static synchronized String source() {
        if (source == null) {
            String generated = RegistryGenerator.generate("workbench.container.l03.gen", "AppRegistry", APP);
            classes = GeneratedCode.compile(NAME, generated, build);
            source = generated;
        }
        return source;
    }

    private static Registry generated() {
        source();
        return GeneratedCode.load(classes, NAME);
    }

    public static class Rota { public Rota(CastList c) {} }
    public static class CastList { public CastList(Rota r) {} }

    /** The checks that make two registries "the same graph". */
    private static void assertWiring(Registry r) {
        BoxOffice office = r.get(BoxOffice.class);
        assertThat(r.get(BoxOffice.class)).isSameAs(office);
        assertThat(office.prices()).isSameAs(r.get(PriceList.class));
        assertThat(office.prices().plan()).isSameAs(r.get(SeatingPlan.class));
        assertThat(office.book()).isSameAs(r.get(SalesBook.class));
        assertThat(office.booking()).isSameAs(r.get(BookingClient.class));
        assertThat(r.get(Basket.class).prices()).isSameAs(office.prices());
        assertThat(r.get(SeatFinder.class).plan()).isSameAs(r.get(SlowPlan.class));
    }

    @Test
    @DisplayName("the generated registry wires the same graph as the reflective container, in the same order")
    void sameGraph() {
        Registry reflective = new Container(APP);
        Registry generated = generated();
        assertWiring(reflective);
        assertWiring(generated);
        assertThat(generated.creationOrder()).isEqualTo(reflective.creationOrder());

        for (Registry r : List.of(reflective, generated)) {           // and it behaves the same
            r.get(BookingScript.class).failures.set(2);
            assertThat(r.get(BoxOffice.class).sell("C12", 12_000)).isEqualTo("hold-C12-12000");
            assertThat(r.get(BookingScript.class).calls.get()).as("booking calls, retries included").isEqualTo(3);
            assertThat(r.get(SalesBook.class).lines()).containsExactly("hold-C12-12000 fee=348");
            assertThat(r.callLog().names()).containsExactly("BookingClient.reserve");
        }
    }

    @Test
    @DisplayName("generated singletons are built on first get, once, after their dependencies")
    void holdersAreLazy() {
        Registry r = generated();
        int plans = SlowPlan.CREATED.get();
        int finders = SeatFinder.CREATED.get();
        r.get(SlowPlan.class);
        assertThat(SlowPlan.CREATED.get() - plans).isEqualTo(1);
        assertThat(SeatFinder.CREATED.get() - finders).as("SeatFinder, which nobody asked for").isZero();
        r.get(SeatFinder.class);
        r.get(SeatFinder.class);
        assertThat(SeatFinder.CREATED.get() - finders).isEqualTo(1);
        assertThat(SlowPlan.CREATED.get() - plans).isEqualTo(1);
    }

    @Test
    @DisplayName("eight threads asking a fresh generated registry at once get one instance, built once")
    void oneInstanceUnderConcurrentFirstAccess() throws Exception {
        Registry r = generated();
        int plans = SlowPlan.CREATED.get();
        int finders = SeatFinder.CREATED.get();
        CountDownLatch go = new CountDownLatch(1);
        Set<Object> seen = Collections.synchronizedSet(Collections.newSetFromMap(new IdentityHashMap<>()));
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            Thread t = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                seen.add(r.get(SeatFinder.class));
            });
            t.start();
            threads.add(t);
        }
        go.countDown();
        for (Thread t : threads) t.join();
        assertThat(seen).hasSize(1);
        assertThat(SlowPlan.CREATED.get() - plans).isEqualTo(1);
        assertThat(SeatFinder.CREATED.get() - finders).isEqualTo(1);
    }

    @Test
    @DisplayName("a generated prototype is new on every get")
    void prototypes() {
        Registry r = generated();
        assertThat(r.get(Basket.class)).isNotSameAs(r.get(Basket.class));
    }

    @Test
    @DisplayName("interception is generated code too: a forwarding class and a subclass, no JDK proxy, no Byte Buddy")
    void generatedProxies() {
        Registry r = generated();
        BookingClient booking = r.get(BookingClient.class);
        assertThat(Proxy.isProxyClass(booking.getClass())).isFalse();
        assertThat(booking.getClass().getName()).isEqualTo(NAME + "$RemoteBookingClient_Proxy");
        assertThat(booking.equals(booking)).isTrue();
        assertThat(booking.reserveStudentSeat("C12")).isEqualTo("hold-C12-5000");

        ShowCloser closer = r.get(ShowCloser.class);
        assertThat(closer.getClass().getName()).isEqualTo(NAME + "$ShowCloser_Intercepted");
        assertThat(closer.close("N-17")).isEqualTo("closed N-17");
        assertThat(r.callLog().names()).containsExactly(
                "BookingClient.reserve", "ShowCloser.verify", "ShowCloser.close");
    }

    @Test
    @DisplayName("the generated source calls constructors directly: no reflection, no class lookups by name")
    void plainCode() {
        assertThat(source())
                .contains("new workbench.container.l03.app.PriceList(SeatingPlan_Holder.INSTANCE)")
                .doesNotContain("java.lang.reflect", "getConstructor", "newInstance", "Class.forName",
                        "ByteBuddy", "Proxy.newProxyInstance", "getAnnotation");
    }

    @Test
    @DisplayName("a cycle fails the build, with the same message the container gives at start-up")
    void cycleFailsTheBuild() {
        assertThatThrownBy(() -> RegistryGenerator.generate("x", "Broken", List.of(Rota.class, CastList.class)))
                .isInstanceOf(ContainerException.class)
                .hasMessage("Dependency cycle: Rota -> CastList -> Rota");
    }
}
