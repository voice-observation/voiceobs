"use client";

import * as React from "react";
import Select, {
  GroupBase,
  MultiValue,
  StylesConfig,
  components,
  OptionProps,
  GroupHeadingProps,
  MenuListProps,
} from "react-select";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

interface TraitOption {
  value: string;
  label: string;
}

interface TraitSelectProps {
  value: string[];
  onChange: (traits: string[]) => void;
  disabled?: boolean;
  placeholder?: string;
}

// Category display names
const CATEGORY_LABELS: Record<string, string> = {
  emotional_state: "Emotional State",
  communication_style: "Communication Style",
  patience_level: "Patience Level",
  cooperation: "Cooperation",
  expertise: "Expertise",
};

// Custom Option component with checkmark
const CustomOption = (props: OptionProps<TraitOption, true, GroupBase<TraitOption>>) => {
  const { isSelected, children } = props;
  return (
    <components.Option {...props}>
      <div className="flex items-center gap-2">
        <div className="flex h-4 w-4 items-center justify-center">
          {isSelected && <Check className="h-4 w-4 text-primary" />}
        </div>
        <span>{children}</span>
      </div>
    </components.Option>
  );
};

// Custom GroupHeading component
const CustomGroupHeading = (
  props: GroupHeadingProps<TraitOption, true, GroupBase<TraitOption>>
) => {
  return <components.GroupHeading {...props}>{props.children}</components.GroupHeading>;
};

// Custom MenuList with explicit scrolling - this is the key fix
const CustomMenuList = (props: MenuListProps<TraitOption, true, GroupBase<TraitOption>>) => {
  const { children, innerRef, innerProps } = props;
  return (
    <div
      ref={innerRef}
      {...innerProps}
      style={{
        maxHeight: "300px",
        overflowY: "auto",
        padding: "4px",
      }}
    >
      {children}
    </div>
  );
};

export function TraitSelect({
  value,
  onChange,
  disabled = false,
  placeholder = "Select traits...",
}: TraitSelectProps) {
  const [vocabulary, setVocabulary] = React.useState<Record<string, string[]>>({});
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // Fetch trait vocabulary on mount
  React.useEffect(() => {
    const fetchVocabulary = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.traits.getTraitVocabulary();
        setVocabulary(response.vocabulary);
      } catch (err) {
        setError("Failed to load traits");
        console.error("Failed to fetch trait vocabulary:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchVocabulary();
  }, []);

  // Convert vocabulary to grouped options
  const groupedOptions: GroupBase<TraitOption>[] = React.useMemo(() => {
    return Object.entries(vocabulary).map(([category, traits]) => ({
      label: CATEGORY_LABELS[category] || category,
      options: traits.map((trait) => ({
        value: trait,
        label: trait,
      })),
    }));
  }, [vocabulary]);

  // Convert value array to selected options
  const selectedOptions: TraitOption[] = React.useMemo(() => {
    return value.map((trait) => ({
      value: trait,
      label: trait,
    }));
  }, [value]);

  const handleChange = (newValue: MultiValue<TraitOption>) => {
    onChange(newValue.map((option) => option.value));
  };

  // Custom styles
  const customStyles: StylesConfig<TraitOption, true, GroupBase<TraitOption>> = {
    control: (base, state) => ({
      ...base,
      backgroundColor: "hsl(var(--background))",
      borderColor: state.isFocused ? "hsl(var(--ring))" : "hsl(var(--border))",
      boxShadow: state.isFocused ? "0 0 0 1px hsl(var(--ring))" : "none",
      "&:hover": {
        borderColor: "hsl(var(--border))",
      },
      minHeight: "40px",
    }),
    menu: (base) => ({
      ...base,
      backgroundColor: "hsl(var(--popover))",
      border: "1px solid hsl(var(--border))",
      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
      zIndex: 9999,
    }),
    menuPortal: (base) => ({
      ...base,
      zIndex: 9999,
    }),
    group: (base) => ({
      ...base,
      paddingTop: "8px",
      paddingBottom: "8px",
    }),
    groupHeading: (base) => ({
      ...base,
      color: "hsl(var(--foreground))",
      fontSize: "13px",
      fontWeight: 600,
      textTransform: "none",
      marginBottom: "6px",
      padding: "6px 8px",
      backgroundColor: "hsl(var(--muted))",
      borderRadius: "4px",
      margin: "0 0 6px 0",
    }),
    option: (base, state) => ({
      ...base,
      backgroundColor: state.isFocused ? "hsl(var(--muted))" : "transparent",
      color: "hsl(var(--popover-foreground))",
      cursor: "pointer",
      borderRadius: "4px",
      padding: "6px 8px",
      "&:active": {
        backgroundColor: "hsl(var(--muted))",
      },
    }),
    multiValue: (base) => ({
      ...base,
      backgroundColor: "hsl(var(--secondary))",
      borderRadius: "4px",
    }),
    multiValueLabel: (base) => ({
      ...base,
      color: "hsl(var(--secondary-foreground))",
      fontSize: "14px",
    }),
    multiValueRemove: (base) => ({
      ...base,
      color: "hsl(var(--secondary-foreground))",
      "&:hover": {
        backgroundColor: "hsl(var(--destructive))",
        color: "hsl(var(--destructive-foreground))",
      },
    }),
    input: (base) => ({
      ...base,
      color: "hsl(var(--foreground))",
    }),
    placeholder: (base) => ({
      ...base,
      color: "hsl(var(--muted-foreground))",
    }),
    indicatorSeparator: (base) => ({
      ...base,
      backgroundColor: "hsl(var(--border))",
    }),
    dropdownIndicator: (base) => ({
      ...base,
      color: "hsl(var(--muted-foreground))",
      "&:hover": {
        color: "hsl(var(--foreground))",
      },
    }),
    clearIndicator: (base) => ({
      ...base,
      color: "hsl(var(--muted-foreground))",
      "&:hover": {
        color: "hsl(var(--foreground))",
      },
    }),
  };

  if (error) {
    return (
      <div className="flex h-10 w-full items-center rounded-md border border-destructive bg-background px-3 py-2 text-sm text-destructive">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <Select<TraitOption, true, GroupBase<TraitOption>>
        isMulti
        options={groupedOptions}
        value={selectedOptions}
        onChange={handleChange}
        isDisabled={disabled}
        isLoading={loading}
        placeholder={placeholder}
        styles={customStyles}
        closeMenuOnSelect={false}
        hideSelectedOptions={false}
        isClearable
        classNamePrefix="trait-select"
        menuPortalTarget={typeof document !== "undefined" ? document.body : null}
        components={{
          Option: CustomOption,
          GroupHeading: CustomGroupHeading,
          MenuList: CustomMenuList,
        }}
      />
      <p
        className={cn(
          "text-xs",
          value.length > 4 ? "text-amber-600 dark:text-amber-500" : "text-muted-foreground"
        )}
      >
        Recommended: 2-4 traits for best persona matching
        {value.length > 4 && ` (${value.length} selected)`}
      </p>
    </div>
  );
}
