
package org.openhab.binding.enocean.internal.config;

import org.openhab.core.binding.BindingConfig;
import org.openhab.model.item.binding.BindingConfigParseException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class BindingConfigParser<TYPE extends BindingConfig> {

    private static final Logger logger = LoggerFactory.getLogger(BindingConfigParser.class);

    /**
     * Parse the configLine into the given config.
     *
     * @param configLine
     * @param config
     * @throws BindingConfigParseException
     */
    public void parse(String configLine, TYPE config) throws BindingConfigParseException {
        configLine = removeFirstBrakets(configLine);
        configLine = removeLastBrakets(configLine);
        String[] entries = configLine.trim().split("[,]");
        for (String entry : entries) {
            String[] entryParts = entry.trim().split("[=]");
            if (entryParts.length != 2) {
                throw new BindingConfigParseException("Each entry must have a key and a value");
            }
            String key = entryParts[0];
            String value = entryParts[1];
            value = removeFirstQuotes(value);
            value = removeLastQuotes(value);
            try {
                config.getClass().getDeclaredField(key).set(config, value);
            } catch (Exception e) {
                logger.error("Could not set value " + value + " to attribute " + key + " in class EnoceanBindingConfig");
            }
        }

    }

    private String removeLastBrakets(String configLine) {
        if (configLine.substring(configLine.length() - 1).equals("}")) {
            return configLine.substring(0, configLine.length() - 1);
        }
        return configLine;
    }

    private String removeFirstBrakets(String configLine) {
        if (configLine.substring(0, 1).equals("{")) {
            return configLine.substring(1);
        }
        return configLine;
    }

    private String removeLastQuotes(String value) {
        if (value.substring(value.length() - 1).equals("\"")) {
            return value.substring(0, value.length() - 1);
        }
        return value;
    }

    private String removeFirstQuotes(String value) {
        if (value.substring(0, 1).equals("\"")) {
            return value.substring(1);
        }
        return value;
    }

}