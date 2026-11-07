package workbench.bytecode.l01;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.lang.management.ManagementFactory;
import java.util.function.Supplier;
import workbench.bytecode.l01.plugin.FxPlugin;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ClassLoadingTest {
    private static final String PREFIX = "workbench.bytecode.l01.plugin.";
    private static final String PLUGIN = PREFIX + "FxPlugin";
    private final ClassLoader app = ClassLoadingTest.class.getClassLoader();

    @BeforeEach
    void clearLog() {
        Events.LOG.clear();
    }

    // ---- part 1: initialization order ----

    @Test
    @DisplayName("FeeSchedule: a known country gets its own fee")
    void knownCountry() {
        assertThat(FeeSchedule.INSTANCE.bpsFor("FR")).isEqualTo(310);
    }

    @Test
    @DisplayName("FeeSchedule: an unknown country gets the 350 bps default, not 0")
    void unknownCountryGetsDefault() {
        assertThat(FeeSchedule.INSTANCE.bpsFor("XX")).isEqualTo(350);
    }

    @Test
    @DisplayName("FeeSchedule: the currency constant is right in every version (javac inlined it)")
    void constantIsInlined() {
        assertThat(FeeSchedule.INSTANCE.currency()).isEqualTo("EUR");
    }

    // ---- part 2: one class file, two loaders ----

    @Test
    @DisplayName("Two loaders define two different Class objects with the same name")
    void twoClassObjects() throws Exception {
        Class<?> a = new IsolatingLoader("A", PREFIX, app).loadClass(PLUGIN);
        Class<?> b = new IsolatingLoader("B", PREFIX, app).loadClass(PLUGIN);
        assertThat(a).isNotSameAs(b);
        assertThat(a.getName()).isEqualTo(b.getName());
        assertThat(a.getClassLoader().getName()).isEqualTo("A");
        assertThat(b.getClassLoader().getName()).isEqualTo("B");
    }

    @Test
    @DisplayName("An instance from loader A is not an instance of B's class, and the cast names both loaders")
    void castAcrossLoadersFails() throws Exception {
        Class<?> a = new IsolatingLoader("A", PREFIX, app).loadClass(PLUGIN);
        Class<?> b = new IsolatingLoader("B", PREFIX, app).loadClass(PLUGIN);
        Object fromA = a.getDeclaredConstructor().newInstance();
        assertThat(b.isInstance(fromA)).isFalse();
        assertThatThrownBy(() -> b.cast(fromA)).isInstanceOf(ClassCastException.class);
        // a real checkcast to the app loader's copy: the JVM's message names both loaders
        assertThatThrownBy(() -> {
            FxPlugin p = (FxPlugin) fromA;
        })
                .isInstanceOf(ClassCastException.class)
                .hasMessageContaining("cannot be cast to class " + PLUGIN)
                .hasMessageContaining("loader 'A'");
        // the interface came from the parent, so both copies share it
        assertThat(((Supplier<?>) fromA).get()).isEqualTo("rates from A");
    }

    @Test
    @DisplayName("Each copy has its own statics: the static initializer ran once per loader")
    void separateStatics() throws Exception {
        Class<?> a = new IsolatingLoader("A", PREFIX, app).loadClass(PLUGIN);
        Class<?> b = new IsolatingLoader("B", PREFIX, app).loadClass(PLUGIN);
        assertThat(a.getField("INITS").getInt(null)).isEqualTo(1);
        assertThat(b.getField("INITS").getInt(null)).isEqualTo(1);
        assertThat(Events.LOG).containsExactlyInAnyOrder("FxPlugin init in A", "FxPlugin init in B");
    }

    @Test
    @DisplayName("Asking one loader twice returns the class it already defined")
    void sameLoaderSameClass() throws Exception {
        IsolatingLoader loader = new IsolatingLoader("A", PREFIX, app);
        assertThat(loader.loadClass(PLUGIN)).isSameAs(loader.loadClass(PLUGIN));
    }

    @Test
    @DisplayName("Classes outside the prefix come from the parent, so the host's classes stay shared")
    void parentFirstOutsidePrefix() throws Exception {
        IsolatingLoader loader = new IsolatingLoader("A", PREFIX, app);
        assertThat(loader.loadClass(Events.class.getName())).isSameAs(Events.class);
        assertThat(loader.loadClass("java.lang.String")).isSameAs(String.class);
    }

    @Test
    @DisplayName("Class.forName(name, false, loader) loads without initializing; a static read initializes")
    void loadIsNotInit() throws Exception {
        var mx = ManagementFactory.getClassLoadingMXBean();
        long before = mx.getTotalLoadedClassCount();
        Class<?> c = Class.forName(PLUGIN, false, new IsolatingLoader("C", PREFIX, app));
        assertThat(mx.getTotalLoadedClassCount()).isGreaterThan(before);
        assertThat(Events.LOG).isEmpty();
        assertThat(c.getField("INITS").getInt(null)).isEqualTo(1);
        assertThat(Events.LOG).containsExactly("FxPlugin init in C");
    }

    @Test
    @DisplayName("A missing plugin class is a ClassNotFoundException")
    void missingClass() {
        IsolatingLoader loader = new IsolatingLoader("A", PREFIX, app);
        assertThatThrownBy(() -> loader.loadClass(PREFIX + "DoesNotExist"))
                .isInstanceOf(ClassNotFoundException.class);
    }
}
