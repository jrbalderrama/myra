# myra(1) completion                                        -*- shell-script -*-

_myra()
{
    local cur prev words cword
    _init_completion || return

    local opts=$(awk -F " " 'BEGIN{ORS=" "}{print $1}' $HOME/.myrarc)
    COMPREPLY=( $( compgen -W "$opts" -- "$cur" ) )

} &&
complete -F _myra myra

# ex: ts=4 sw=4 et filetype=sh
