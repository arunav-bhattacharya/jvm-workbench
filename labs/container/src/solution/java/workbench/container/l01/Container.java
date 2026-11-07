package workbench.container.l01;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * A tiny dependency injection container. It checks the whole graph when it is built, and creates
 * each component the first time someone needs it.
 */
public final class Container {
    private final BeanGraph graph;
    private final List<Class<?>> order;
    private final Map<Class<?>, SingletonCell<Object>> singletons;   // filled once here, never changed: safe to share

    public Container(Collection<Class<?>> components) {
        this.graph = new BeanGraph(components);
        this.order = graph.creationOrder();          // fail fast: cycles, missing and ambiguous dependencies
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

    public <T> T get(Class<T> type) {
        return type.cast(instanceOf(graph.implementationFor(type)));
    }

    private Object instanceOf(Class<?> component) {
        SingletonCell<Object> cell = singletons.get(component);
        return cell != null ? cell.get() : create(component);     // no cell: a prototype, new every time
    }

    private Object create(Class<?> component) {
        Constructor<?> constructor = Constructors.pick(component);
        Object[] args = graph.dependenciesOf(component).stream().map(this::instanceOf).toArray();
        try {
            return constructor.newInstance(args);
        } catch (InvocationTargetException e) {
            throw new ContainerException("constructor of " + component.getSimpleName() + " failed", e.getCause());
        } catch (ReflectiveOperationException e) {
            throw new ContainerException("could not create " + component.getSimpleName(), e);
        }
    }
}
