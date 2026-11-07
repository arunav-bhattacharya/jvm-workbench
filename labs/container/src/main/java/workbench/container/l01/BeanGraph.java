package workbench.container.l01;

import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * The components and who needs whom. Each component is bound to its own class and to every
 * interface it implements directly; a constructor parameter is resolved through those bindings.
 */
public final class BeanGraph {
    private final List<Class<?>> components;
    private final Map<Class<?>, List<Class<?>>> providers = new LinkedHashMap<>();   // type -> components bound to it

    public BeanGraph(Collection<Class<?>> components) {
        this.components = List.copyOf(components);
        for (Class<?> c : this.components) {
            if (c.isInterface() || Modifier.isAbstract(c.getModifiers())) {
                throw new ContainerException(c.getSimpleName() + " is abstract; a component must be a concrete class");
            }
            providers.computeIfAbsent(c, k -> new ArrayList<>()).add(c);
            for (Class<?> i : c.getInterfaces()) providers.computeIfAbsent(i, k -> new ArrayList<>()).add(c);
        }
    }

    public List<Class<?>> components() {
        return components;
    }

    /** The one component bound to {@code type}. */
    public Class<?> implementationFor(Class<?> type) {
        List<Class<?>> found = providers.getOrDefault(type, List.of());
        if (found.isEmpty()) throw new ContainerException("No component provides " + type.getSimpleName());
        if (found.size() > 1) {
            throw new ContainerException(found.size() + " components provide " + type.getSimpleName() + ": "
                    + found.stream().map(Class::getSimpleName).toList());
        }
        return found.get(0);
    }

    /** The components a component's constructor needs, in parameter order. */
    public List<Class<?>> dependenciesOf(Class<?> component) {
        List<Class<?>> deps = new ArrayList<>();
        for (Class<?> p : Constructors.pick(component).getParameterTypes()) {
            try {
                deps.add(implementationFor(p));
            } catch (ContainerException e) {
                throw new ContainerException(component.getSimpleName() + " needs " + p.getSimpleName() + ": " + e.getMessage());
            }
        }
        return deps;
    }

    /**
     * Every component once, each one after everything it depends on.
     *
     * <p>Walk the graph depth first, starting from each component in {@link #components()} order.
     * Add a component to the result only after all of {@link #dependenciesOf} are in it (post-order),
     * and skip components that are already in it. Keep the components you are still inside on a
     * path; meeting one of them again is a cycle. Throw a {@link ContainerException} whose message
     * names the cycle, starting and ending at the repeated class:
     * {@code "Dependency cycle: Ledger -> AuditTrail -> Ledger"} (simple names).
     */
    public List<Class<?>> creationOrder() {
        throw new UnsupportedOperationException("TODO: depth-first, post-order, with cycle detection");
    }
}
