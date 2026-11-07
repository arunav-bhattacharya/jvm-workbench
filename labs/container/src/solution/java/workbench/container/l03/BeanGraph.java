package workbench.container.l03;

import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

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

    /** The types that resolve to {@code component}: its own class, and each interface only it implements. */
    public List<Class<?>> typesBoundTo(Class<?> component) {
        List<Class<?>> types = new ArrayList<>();
        providers.forEach((type, found) -> {
            if (found.size() == 1 && found.get(0) == component) types.add(type);
        });
        return types;
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

    /** Every component once, each one after everything it depends on. */
    public List<Class<?>> creationOrder() {
        List<Class<?>> order = new ArrayList<>();
        Set<Class<?>> done = new HashSet<>();
        Set<Class<?>> path = new LinkedHashSet<>();     // the components we are inside right now, in order
        for (Class<?> c : components) visit(c, done, path, order);
        return List.copyOf(order);
    }

    private void visit(Class<?> c, Set<Class<?>> done, Set<Class<?>> path, List<Class<?>> order) {
        if (done.contains(c)) return;                   // 1. already placed: shared dependencies appear once
        if (path.contains(c)) throw cycle(path, c);     // 2. we are back at a class we are still building
        path.add(c);
        for (Class<?> d : dependenciesOf(c)) visit(d, done, path, order);
        path.remove(c);
        done.add(c);
        order.add(c);                                   // 3. post-order: after all of its dependencies
    }

    private static ContainerException cycle(Set<Class<?>> path, Class<?> back) {
        List<String> names = new ArrayList<>();
        boolean inCycle = false;
        for (Class<?> p : path) {
            if (p == back) inCycle = true;              // start at the repeated class, not at the root
            if (inCycle) names.add(p.getSimpleName());
        }
        names.add(back.getSimpleName());
        return new ContainerException("Dependency cycle: " + String.join(" -> ", names));
    }
}
