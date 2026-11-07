package workbench.startup.l03;

import java.lang.reflect.Executable;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Builds GraalVM reachability metadata (schema v1.2.0) as plain maps and lists, the same shape
 * as the JSON in {@code META-INF/native-image/<groupId>/<artifactId>/reachability-metadata.json}.
 */
public final class MetadataWriter {
    private MetadataWriter() {
    }

    /**
     * One reflection entry that registers exactly the given constructors and methods of {@code type}:
     * <pre>
     * {"type": "workbench.startup.l03.PaymentAuthorized",
     *  "methods": [{"name": "&lt;init&gt;", "parameterTypes": ["java.lang.String", "long"]},
     *              {"name": "paymentId", "parameterTypes": []}]}
     * </pre>
     *
     * <p>TODO:
     * <ul>
     *   <li>"type" is {@code type.getName()};</li>
     *   <li>one "methods" item per member, in argument order: a {@code Constructor} is named
     *       {@code "<init>"}, a {@code Method} by its name;</li>
     *   <li>"parameterTypes" lists {@code getName()} of each parameter type: "java.lang.String", "long";</li>
     *   <li>throw {@code IllegalArgumentException} if a member is declared by another class.</li>
     * </ul>
     */
    public static Map<String, Object> reflection(Class<?> type, Executable... members) {
        throw new UnsupportedOperationException("TODO: build the reflection entry");
    }

    /**
     * One entry for a JDK dynamic proxy: {@code {"type": {"proxy": ["a.First", "b.Second"]}}}, with the
     * interface names in the order given, because a proxy for (A, B) is a different class from (B, A).
     *
     * <p>TODO: throw {@code IllegalArgumentException} for a class that is not an interface and for an
     * interface listed twice, the same rules {@code java.lang.reflect.Proxy} enforces.
     */
    public static Map<String, Object> proxy(Class<?>... interfaces) {
        throw new UnsupportedOperationException("TODO: build the proxy entry");
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
