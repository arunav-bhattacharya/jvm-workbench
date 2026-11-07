package workbench.container.l02;

import java.lang.reflect.Constructor;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * The container from lesson 1, with one change: {@link Interception} builds every component, so a
 * component can come back as itself, as a JDK proxy, or as a Byte Buddy subclass.
 */
public final class Container {
    private final BeanGraph graph;
    private final Interception interception;
    private final List<Class<?>> order;
    private final Map<Class<?>, SingletonCell<Object>> singletons;   // filled once here, never changed: safe to share

    public Container(Collection<Class<?>> components) {
        this(components, new Interception());
    }

    public Container(Collection<Class<?>> components, Interception interception) {
        this.graph = new BeanGraph(components);
        this.interception = interception;
        this.order = graph.creationOrder();          // fail fast: cycles, missing and ambiguous dependencies
        for (Class<?> c : order) interception.check(c);   // fail fast: a component that can't be intercepted
        Map<Class<?>, SingletonCell<Object>> cells = new HashMap<>();
        for (Class<?> c : order) {
            if (scopeOf(c) == Scope.SINGLETON) cells.put(c, new SingletonCell<>(() -> create(c)));
        }
        this.singletons = Map.copyOf(cells);
    }

    /** A container for every {@code @Component} class in one package. */
    public static Container scan(String packageName) {
        return new Container(ClassScanner.scan(Container.class.getClassLoader(), packageName));
    }

    /** The scope on the {@code @Component} annotation; a class listed without one is a singleton. */
    static Scope scopeOf(Class<?> component) {
        Component annotation = component.getAnnotation(Component.class);
        return annotation == null ? Scope.SINGLETON : annotation.scope();
    }

    public List<Class<?>> creationOrder() {
        return order;
    }

    public CallLog callLog() {
        return interception.getLog();
    }

    public <T> T get(Class<T> type) {
        return type.cast(resolve(type));
    }

    private Object resolve(Class<?> type) {
        Class<?> component = graph.implementationFor(type);
        Object bean = instanceOf(component);
        if (!type.isInstance(bean)) {                // a JDK proxy implements the interfaces, not the class
            throw new ContainerException(component.getSimpleName() + " is behind a JDK proxy that implements "
                    + Arrays.stream(component.getInterfaces()).map(Class::getSimpleName).toList()
                    + "; ask for one of those, not for the class");
        }
        return bean;
    }

    private Object instanceOf(Class<?> component) {
        SingletonCell<Object> cell = singletons.get(component);
        return cell != null ? cell.get() : create(component);     // no cell: a prototype, new every time
    }

    private Object create(Class<?> component) {
        Constructor<?> constructor = Constructors.pick(component);
        Object[] args = Arrays.stream(constructor.getParameterTypes()).map(this::resolve).toArray();
        return interception.create(component, constructor, args);
    }
}
