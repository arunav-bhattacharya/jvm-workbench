package workbench.startup.l03;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Just enough JSON for the tests: objects become maps, arrays lists, numbers Long or Double. */
final class MiniJson {
    private final String s;
    private int i;

    private MiniJson(String s) {
        this.s = s;
    }

    static Object parse(String text) {
        MiniJson p = new MiniJson(text);
        Object v = p.value();
        p.ws();
        if (p.i != p.s.length()) throw p.error("trailing text");
        return v;
    }

    private Object value() {
        ws();
        if (i >= s.length()) throw error("unexpected end");
        char c = s.charAt(i);
        if (c == '{') return object();
        if (c == '[') return array();
        if (c == '"') return string();
        if (s.startsWith("true", i)) { i += 4; return true; }
        if (s.startsWith("false", i)) { i += 5; return false; }
        if (s.startsWith("null", i)) { i += 4; return null; }
        return number();
    }

    private Map<String, Object> object() {
        Map<String, Object> m = new LinkedHashMap<>();
        i++;
        ws();
        if (peek('}')) return m;
        do {
            ws();
            String key = string();
            ws();
            expect(':');
            if (m.put(key, value()) != null) throw error("duplicate key " + key);
            ws();
        } while (next(','));
        expect('}');
        return m;
    }

    private List<Object> array() {
        List<Object> l = new ArrayList<>();
        i++;
        ws();
        if (peek(']')) return l;
        do {
            l.add(value());
            ws();
        } while (next(','));
        expect(']');
        return l;
    }

    private String string() {
        expect('"');
        StringBuilder b = new StringBuilder();
        while (i < s.length() && s.charAt(i) != '"') {
            char c = s.charAt(i++);
            if (c == '\\') {
                char e = s.charAt(i++);
                switch (e) {
                    case 'n' -> b.append('\n');
                    case 't' -> b.append('\t');
                    case 'u' -> { b.append((char) Integer.parseInt(s.substring(i, i + 4), 16)); i += 4; }
                    default -> b.append(e);
                }
            } else {
                b.append(c);
            }
        }
        expect('"');
        return b.toString();
    }

    private Number number() {
        int start = i;
        while (i < s.length() && "+-0123456789.eE".indexOf(s.charAt(i)) >= 0) i++;
        String n = s.substring(start, i);
        if (n.isEmpty()) throw error("unexpected character");
        return n.matches("-?\\d+") ? (Number) Long.parseLong(n) : (Number) Double.parseDouble(n);
    }

    private void ws() {
        while (i < s.length() && Character.isWhitespace(s.charAt(i))) i++;
    }

    private boolean peek(char c) {
        if (i < s.length() && s.charAt(i) == c) { i++; return true; }
        return false;
    }

    private boolean next(char c) {
        ws();
        return peek(c);
    }

    private void expect(char c) {
        ws();
        if (!peek(c)) throw error("expected '" + c + "'");
    }

    private IllegalArgumentException error(String what) {
        return new IllegalArgumentException("bad JSON at offset " + i + ": " + what);
    }
}
