import React, { forwardRef, createContext, useContext, useId } from 'react';
import { cn } from '../../lib/utils';
import { Label } from './label';
import { Input } from './input';
import { Textarea } from './textarea';
import { Button } from './button';
import { Alert, AlertDescription } from './alert';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';

// Form Context for accessibility
const FormFieldContext = createContext({});

// Enhanced Form Field with full a11y support
export const FormField = forwardRef(({
  children,
  label,
  error,
  hint,
  required = false,
  className,
  ...props
}, ref) => {
  const id = useId();
  const labelId = `${id}-label`;
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  
  const contextValue = {
    id,
    labelId,
    errorId,
    hintId,
    hasError: !!error,
    isRequired: required,
    describedBy: [
      hint && hintId,
      error && errorId
    ].filter(Boolean).join(' ') || undefined
  };

  return (
    <FormFieldContext.Provider value={contextValue}>
      <div className={cn('space-y-2', className)} {...props} ref={ref}>
        {label && (
          <Label 
            id={labelId}
            htmlFor={id}
            className={cn(
              'kuryecini-label',
              required && 'after:content-["*"] after:text-destructive after:ml-1',
              error && 'text-destructive'
            )}
          >
            {label}
          </Label>
        )}
        
        {hint && (
          <p 
            id={hintId}
            className="text-sm text-muted-foreground"
          >
            {hint}
          </p>
        )}
        
        {children}
        
        {error && (
          <Alert variant="destructive" id={errorId} role="alert" aria-live="polite">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </div>
    </FormFieldContext.Provider>
  );
});

FormField.displayName = 'FormField';

// Enhanced Input with accessibility
export const AccessibleInput = forwardRef(({
  className,
  type = 'text',
  ...props
}, ref) => {
  const { 
    id, 
    hasError, 
    isRequired, 
    describedBy 
  } = useContext(FormFieldContext);

  return (
    <Input
      ref={ref}
      id={id}
      type={type}
      aria-invalid={hasError}
      aria-required={isRequired}
      aria-describedby={describedBy}
      className={cn(
        'kuryecini-input',
        hasError && 'border-destructive focus-visible:ring-destructive',
        className
      )}
      {...props}
    />
  );
});

AccessibleInput.displayName = 'AccessibleInput';

// Enhanced Textarea with accessibility
export const AccessibleTextarea = forwardRef(({
  className,
  ...props
}, ref) => {
  const { 
    id, 
    hasError, 
    isRequired, 
    describedBy 
  } = useContext(FormFieldContext);

  return (
    <Textarea
      ref={ref}
      id={id}
      aria-invalid={hasError}
      aria-required={isRequired}
      aria-describedby={describedBy}
      className={cn(
        'kuryecini-input min-h-[100px]',
        hasError && 'border-destructive focus-visible:ring-destructive',
        className
      )}
      {...props}
    />
  );
});

AccessibleTextarea.displayName = 'AccessibleTextarea';

// Enhanced Button with loading and accessibility states
export const AccessibleButton = forwardRef(({
  children,
  loading = false,
  loadingText = 'Yükleniyor...',
  variant = 'default',
  className,
  disabled,
  ...props
}, ref) => {
  const isDisabled = disabled || loading;

  return (
    <Button
      ref={ref}
      variant={variant}
      disabled={isDisabled}
      aria-busy={loading}
      aria-label={loading ? loadingText : undefined}
      className={cn(
        'relative transition-all duration-200',
        'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      {...props}
    >
      {loading && (
        <span className="absolute inset-0 flex items-center justify-center">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          <span className="sr-only">{loadingText}</span>
        </span>
      )}
      <span className={loading ? 'invisible' : ''}>
        {children}
      </span>
    </Button>
  );
});

AccessibleButton.displayName = 'AccessibleButton';

// Form Success Message
export const FormSuccess = ({ message, className, ...props }) => (
  <Alert className={cn('border-success bg-success/10', className)} role="alert" aria-live="polite" {...props}>
    <CheckCircle className="h-4 w-4 text-success" />
    <AlertDescription className="text-success-foreground">
      {message}
    </AlertDescription>
  </Alert>
);

// Form Info Message  
export const FormInfo = ({ message, className, ...props }) => (
  <Alert className={cn('border-info bg-info/10', className)} role="status" aria-live="polite" {...props}>
    <Info className="h-4 w-4 text-info" />
    <AlertDescription className="text-info-foreground">
      {message}
    </AlertDescription>
  </Alert>
);

// Enhanced Select with accessibility
export const AccessibleSelect = forwardRef(({
  children,
  placeholder = 'Seçiniz...',
  className,
  ...props
}, ref) => {
  const { 
    id, 
    hasError, 
    isRequired, 
    describedBy 
  } = useContext(FormFieldContext);

  return (
    <select
      ref={ref}
      id={id}
      aria-invalid={hasError}
      aria-required={isRequired}
      aria-describedby={describedBy}
      className={cn(
        'kuryecini-input cursor-pointer',
        hasError && 'border-destructive focus-visible:ring-destructive',
        className
      )}
      {...props}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {children}
    </select>
  );
});

AccessibleSelect.displayName = 'AccessibleSelect';

// Checkbox with accessibility
export const AccessibleCheckbox = forwardRef(({
  label,
  description,
  error,
  className,
  ...props
}, ref) => {
  const id = useId();
  const errorId = `${id}-error`;
  const descId = `${id}-desc`;

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-start space-x-2">
        <input
          ref={ref}
          id={id}
          type="checkbox"
          aria-invalid={!!error}
          aria-describedby={[
            description && descId,
            error && errorId
          ].filter(Boolean).join(' ') || undefined}
          className={cn(
            'h-4 w-4 rounded border border-input bg-background text-primary',
            'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
            'disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-destructive'
          )}
          {...props}
        />
        <div className="space-y-1">
          {label && (
            <Label 
              htmlFor={id}
              className={cn(
                'cursor-pointer',
                error && 'text-destructive'
              )}
            >
              {label}
            </Label>
          )}
          {description && (
            <p id={descId} className="text-sm text-muted-foreground">
              {description}
            </p>
          )}
        </div>
      </div>
      
      {error && (
        <Alert variant="destructive" id={errorId} role="alert" aria-live="polite">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
});

AccessibleCheckbox.displayName = 'AccessibleCheckbox';

// Radio Group with accessibility
export const AccessibleRadioGroup = ({
  legend,
  options = [],
  value,
  onChange,
  error,
  required = false,
  className,
  ...props
}) => {
  const id = useId();
  const errorId = `${id}-error`;

  return (
    <fieldset
      className={cn('space-y-3', className)}
      aria-invalid={!!error}
      aria-describedby={error ? errorId : undefined}
      {...props}
    >
      {legend && (
        <legend className={cn(
          'kuryecini-label text-base font-medium',
          required && 'after:content-["*"] after:text-destructive after:ml-1',
          error && 'text-destructive'
        )}>
          {legend}
        </legend>
      )}
      
      <div className="space-y-2">
        {options.map((option) => {
          const optionId = `${id}-${option.value}`;
          return (
            <div key={option.value} className="flex items-center space-x-2">
              <input
                id={optionId}
                type="radio"
                name={id}
                value={option.value}
                checked={value === option.value}
                onChange={(e) => onChange?.(e.target.value)}
                className={cn(
                  'h-4 w-4 border border-input text-primary',
                  'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              />
              <Label htmlFor={optionId} className="cursor-pointer">
                {option.label}
              </Label>
            </div>
          );
        })}
      </div>
      
      {error && (
        <Alert variant="destructive" id={errorId} role="alert" aria-live="polite">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </fieldset>
  );
});

AccessibleRadioGroup.displayName = 'AccessibleRadioGroup';

// Focus Ring utility component
export const FocusRing = ({ children, className, ...props }) => (
  <div 
    className={cn(
      'focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 rounded-md',
      className
    )} 
    {...props}
  >
    {children}
  </div>
);

export {
  FormField,
  AccessibleInput,
  AccessibleTextarea,
  AccessibleButton,
  AccessibleSelect,
  AccessibleCheckbox,
  AccessibleRadioGroup,
  FormSuccess,
  FormInfo,
  FocusRing
};