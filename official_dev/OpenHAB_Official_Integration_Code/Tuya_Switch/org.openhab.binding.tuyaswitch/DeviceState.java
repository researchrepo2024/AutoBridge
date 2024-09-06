
package org.openhab.binding.tuya.internal.data;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.Date;
import java.util.function.BiConsumer;

import org.openhab.binding.tuya.internal.annotations.Channel;
import org.openhab.binding.tuya.internal.discovery.DeviceDescriptor;
import org.openhab.binding.tuya.internal.net.QueueItem;
import org.openhab.core.library.types.DecimalType;
import org.openhab.core.library.types.HSBType;
import org.openhab.core.library.types.OnOffType;
import org.openhab.core.library.types.PercentType;
import org.openhab.core.types.Command;
import org.openhab.core.types.State;

import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;


public class DeviceState {

    // To convert objects to a json String.
    private static final Gson GSON = new Gson();

    // Empty array ready to use.
    private static final Object[] EMPTY_ARRAY = new Object[0];

    // The device ID.
    private String devId;

    @SerializedName("t")
    long time;

    public DeviceState() {
    }

    public DeviceState(DeviceDescriptor deviceDescriptor) {
        this.devId = deviceDescriptor == null ? "" : deviceDescriptor.getGwId();
        this.time = new Date().getTime() / 1000;
    }

    // Conversion methods to be used in subclasses.

    protected OnOffType toOnOffType(Boolean bool) {
        return bool == null ? null : bool ? OnOffType.ON : OnOffType.OFF;
    }

    protected Boolean toBoolean(Command command) {
        if (command instanceof OnOffType) {
            return command == OnOffType.ON;
        } else {
            return null;
        }
    }

    /**
     * Take an OH command, and try to calculate the value as and integer
     * from 0 to 255. This is used to convert dimmer commands to the 0..255 value used by the Tuya devices.
     *
     * @param command the OH command.
     * @return the numeric value in the range 0..255.
     */
    protected Integer toInt8(Command command) {
        if (command instanceof PercentType) {
            return (int) ((Math.round(((PercentType) (command)).intValue() * 255 / 100)) & 0xFF);
        } else if (command instanceof Number) {
            return (int) ((Math.round(((Number) (command)).doubleValue() * 255)) & 0xFF);
        } else {
            return null;
        }
    }

    /**
     * Convert from a long value to a DecimalType indicating dimmer values.
     *
     * @param value the long must be in the rande 0..255.
     * @return the DecimalType in the range 0..1.
     */
    protected DecimalType toDecimalType(long value) {
        return new DecimalType(value / 255.0);
    }

    /**
     * Take an OH command represented as Color (HSBType) and convert it to a Tuya understandable RGB value.
     *
     * @param hsb the color to encode.
     * @return the command string.
     */
    protected String toColorString(Command command) {
        if (command instanceof HSBType) {
            HSBType hsb = (HSBType) command;
            StringBuilder b = new StringBuilder();
            b.append(Integer.toHexString(hsb.getRed().intValue() * 255 / 100))
                    .append(Integer.toHexString(hsb.getGreen().intValue() * 255 / 100))
                    .append(Integer.toHexString(hsb.getBlue().intValue() * 255 / 100)).append("00f1ffff");// append("016500ff");
            return b.toString();
        } else {
            return null;
        }
    }

    /**
     * Traverse through all changed properties and invoke the handler.
     *
     * @param handler
     */
    @SuppressWarnings("null")
    public void forChangedProperties(BiConsumer<String, State> handler) {
        Class<?> theClass = this.getClass();
        while (theClass != Object.class) {
            for (Method method : theClass.getDeclaredMethods()) {
                Channel channel = method.getAnnotation(Channel.class);
                if (channel != null) {
                    if (State.class.isAssignableFrom(method.getReturnType())) {
                        try {
                            State state = (State) method.invoke(this, EMPTY_ARRAY);
                            if (state != null) {
                                handler.accept(channel.value(), state);
                            }
                        } catch (IllegalAccessException | IllegalArgumentException | InvocationTargetException e) {
                            // Silently ignore this
                            System.out.println(e);
                        }
                    }
                }
            }
            theClass = theClass.getSuperclass();
        }
    }

    public String getDevId() {
        return devId;
    }

    public long getTime() {
        return time;
    }

    public void setTime(long time) {
        this.time = time;
    }

    /**
     * Return true when the given QueueItem is conflicting with this item. This test is used to remove conflicting items
     * from the queue. An example is a switch that may be on or off, and it makes no sense to have both an on and an off
     * command in the queue at the same time.
     *
     * @param other the item to compare to.
     * @return true when conflicting.
     */
    public boolean isConflicting(QueueItem other) {
        return false;
    }

    /**
     * Return the json representation as a String.
     *
     * @return the json String.
     */
    public String toJson() {
        return GSON.toJson(this);
    }
}