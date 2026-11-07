package workbench.container.l03;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

/**
 * Writes, as Java source, the class that intercepts one component: a forwarding class for a component
 * with interfaces, or a subclass for one without. It reads the annotations now, at build time, so
 * the generated code needs no reflection when it runs. Given complete: read it, you don't need to change it.
 */
final class ProxySource {
    private ProxySource() {}

    /** The name of the generated class for {@code component}, or null when it needs none. */
    static String className(Class<?> component) {
        if (!needsProxy(component)) return null;
        return component.getSimpleName() + (component.getInterfaces().length > 0 ? "_Proxy" : "_Intercepted");
    }

    static boolean needsProxy(Class<?> component) {
        return !interceptedMethods(component).isEmpty();
    }

    /** The source of the nested class, or "" when the component is used as it is. */
    static String emit(Class<?> component) {
        if (!needsProxy(component)) return "";
        Interception check = new Interception();
        check.check(component);                                   // same refusals as at run time, now at build time
        return component.getInterfaces().length > 0 ? forwarder(component) : subclass(component);
    }

    private static List<Method> interceptedMethods(Class<?> component) {
        Class<?>[] interfaces = component.getInterfaces();
        List<Method> candidates = interfaces.length > 0
                ? Arrays.stream(interfaces).flatMap(i -> Arrays.stream(i.getMethods())).toList()
                : Arrays.asList(component.getMethods());
        return candidates.stream().filter(Interception::isIntercepted).filter(m -> !m.isDefault()).toList();
    }

    /** A class that implements the interfaces and forwards to a target; default methods are inherited. */
    private static String forwarder(Class<?> component) {
        String name = className(component);
        String target = component.getCanonicalName();
        StringBuilder out = new StringBuilder();
        out.append("    static final class ").append(name).append(" implements ")
                .append(Arrays.stream(component.getInterfaces()).map(Class::getCanonicalName).collect(Collectors.joining(", ")))
                .append(" {\n");
        List<Method> abstracts = new ArrayList<>();
        for (Class<?> i : component.getInterfaces()) {
            for (Method m : i.getMethods()) if (Modifier.isAbstract(m.getModifiers())) abstracts.add(m);
        }
        appendChains(out, abstracts);
        out.append("        private final ").append(target).append(" target;\n\n");
        out.append("        ").append(name).append("(").append(target).append(" target) {\n")
                .append("            this.target = target;\n        }\n\n");
        for (Method m : abstracts) appendMethod(out, abstracts.indexOf(m), m, "target");
        // equals and hashCode stay Object's: identity, which is what a proxy owes its callers
        out.append("        @Override\n        public String toString() {\n            return \"Proxy[\" + target + \"]\";\n        }\n");
        return out.append("    }\n\n").toString();
    }

    /** A subclass that overrides the intercepted methods and calls super at the end of the chain. */
    private static String subclass(Class<?> component) {
        String name = className(component);
        Class<?>[] params = Constructors.pick(component).getParameterTypes();
        StringBuilder out = new StringBuilder();
        out.append("    static final class ").append(name).append(" extends ").append(component.getCanonicalName()).append(" {\n");
        List<Method> intercepted = interceptedMethods(component);
        appendChains(out, intercepted);
        out.append("        ").append(name).append("(").append(parameters(params)).append(")")
                .append(throwsClause(Constructors.pick(component).getExceptionTypes())).append(" {\n")
                .append("            super(").append(arguments(params.length)).append(");\n        }\n\n");
        for (Method m : intercepted) appendMethod(out, intercepted.indexOf(m), m, "super");
        return out.append("    }\n\n").toString();
    }

    private static void appendChains(StringBuilder out, List<Method> methods) {
        for (int i = 0; i < methods.size(); i++) {
            Method m = methods.get(i);
            if (!Interception.isIntercepted(m)) continue;
            Retry retry = m.getAnnotation(Retry.class);
            String retryOn = retry == null ? "" : Arrays.stream(retry.on())
                    .map(k -> ", " + k.getCanonicalName() + ".class")
                    .collect(Collectors.joining());
            out.append("        private static final java.util.List<Interceptor> CHAIN_").append(i)
                    .append(" = INTERCEPTION.chain(").append(m.isAnnotationPresent(Timed.class)).append(", ")
                    .append(retry == null ? 0 : retry.attempts()).append(retryOn).append(");\n");
        }
        out.append("\n");
    }

    private static void appendMethod(StringBuilder out, int index, Method m, String receiver) {
        Class<?> ret = m.getReturnType();
        String call = receiver + "." + m.getName() + "(" + arguments(m.getParameterCount()) + ")";
        out.append("        @Override\n        public ").append(ret.getCanonicalName()).append(" ").append(m.getName())
                .append("(").append(parameters(m.getParameterTypes())).append(")").append(throwsClause(m.getExceptionTypes())).append(" {\n");
        if (!Interception.isIntercepted(m)) {                    // not intercepted: forward directly
            out.append("            ").append(ret == void.class ? "" : "return ").append(call).append(";\n        }\n\n");
            return;
        }
        String args = "new Object[] {" + arguments(m.getParameterCount()) + "}";
        String body = ret == void.class ? "() -> { " + call + "; return null; }" : "() -> " + call;
        String invocation = "new Invocation(\"" + Interception.nameOf(m) + "\", " + args + ", CHAIN_" + index + ", " + body + ").proceed()";
        if (ret == void.class) out.append("            ").append(invocation).append(";\n");
        else out.append("            return (").append(boxed(ret).getCanonicalName()).append(") ").append(invocation).append(";\n");
        out.append("        }\n\n");
    }

    private static String parameters(Class<?>[] types) {
        return IntStream.range(0, types.length).mapToObj(i -> types[i].getCanonicalName() + " p" + i).collect(Collectors.joining(", "));
    }

    private static String arguments(int count) {
        return IntStream.range(0, count).mapToObj(i -> "p" + i).collect(Collectors.joining(", "));
    }

    private static String throwsClause(Class<?>[] exceptions) {
        if (exceptions.length == 0) return "";
        return " throws " + Arrays.stream(exceptions).map(Class::getCanonicalName).collect(Collectors.joining(", "));
    }

    private static Class<?> boxed(Class<?> type) {
        if (!type.isPrimitive()) return type;
        return switch (type.getName()) {
            case "int" -> Integer.class;
            case "long" -> Long.class;
            case "boolean" -> Boolean.class;
            case "double" -> Double.class;
            case "float" -> Float.class;
            case "short" -> Short.class;
            case "byte" -> Byte.class;
            default -> Character.class;
        };
    }
}
