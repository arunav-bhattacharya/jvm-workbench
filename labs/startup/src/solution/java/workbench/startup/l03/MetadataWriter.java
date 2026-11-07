package workbench.startup.l03;

import java.lang.reflect.Constructor;
import java.lang.reflect.Executable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Builds GraalVM reachability metadata (schema v1.2.0) as plain maps and lists, the same shape
 * as the JSON in {@code META-INF/native-image/<groupId>/<artifactId>/reachability-metadata.json}.
 */
public final class MetadataWriter {
    private MetadataWriter() {
    }

    /** One reflection entry that registers exactly the given constructors and methods of {@code type}. */
    public static Map<String, Object> reflection(Class<?> type, Executable... members) {
        List<Map<String, Object>> methods = new ArrayList<>();
        for (Executable m : members) {
            if (m.getDeclaringClass() != type) {
                throw new IllegalArgumentException(m + " is not declared by " + type.getName());
            }
            Map<String, Object> method = new LinkedHashMap<>();
            // 1. constructors go by the JVM's name for them
            method.put("name", m instanceof Constructor<?> ? "<init>" : m.getName());
            // 2. Class.getName gives "java.lang.String" and "long", the form the schema uses
            method.put("parameterTypes", Arrays.stream(m.getParameterTypes()).map(Class::getName).toList());
            methods.add(method);
        }
        Map<String, Object> entry = new LinkedHashMap<>();
        entry.put("type", type.getName());
        entry.put("methods", methods);
        return entry;
    }

    /** One entry for a JDK dynamic proxy, interfaces in the given order. */
    public static Map<String, Object> proxy(Class<?>... interfaces) {
        Set<Class<?>> seen = new HashSet<>();
        List<String> names = new ArrayList<>();
        for (Class<?> i : interfaces) {
            if (!i.isInterface()) {
                throw new IllegalArgumentException(i.getName() + " is not an interface");  // Proxy's rule too
            }
            if (!seen.add(i)) {
                throw new IllegalArgumentException("repeated interface: " + i.getName());
            }
            names.add(i.getName());                       // 3. order kept: (A, B) and (B, A) are different classes
        }
        return Map.of("type", Map.of("proxy", List.copyOf(names)));
    }

    /** A whole file: {@code {"reflection": [entries...]}}. Already done. */
    public static Map<String, Object> document(List<Map<String, Object>> reflectionEntries) {
        Map<String, Object> doc = new LinkedHashMap<>();
        doc.put("reflection", List.copyOf(reflectionEntries));
        return doc;
    }

    /** Writes maps, lists, strings, numbers and booleans as JSON. Already done. */
    public static String toJson(Object value) {
        if (value instanceof Map<?, ?> map) {
            return map.entrySet().stream()
                    .map(e -> toJson(String.valueOf(e.getKey())) + ": " + toJson(e.getValue()))
                    .collect(Collectors.joining(", ", "{", "}"));
        }
        if (value instanceof List<?> list) {
            return list.stream().map(MetadataWriter::toJson).collect(Collectors.joining(", ", "[", "]"));
        }
        if (value instanceof String s) {
            return '"' + s.replace("\\", "\\\\").replace("\"", "\\\"") + '"';
        }
        return String.valueOf(value);
    }
}
